import pytest
from fastapi.testclient import TestClient

import web.app as server

client = TestClient(server.app)


def start(answer="crane"):
    res = client.post("/api/games")
    assert res.status_code == 201
    game_id = res.json()["id"]
    server.games[game_id].answer = answer  # pin the hidden word so tests are deterministic
    return game_id


def guess(game_id, word):
    return client.post(f"/api/games/{game_id}/guesses", json={"guess": word})


def test_index_page():
    res = client.get("/")
    assert res.status_code == 200
    assert "WORDLE LAB" in res.text


def test_new_game():
    data = client.post("/api/games").json()
    assert data["max_guesses"] == 6
    assert data["remaining"] == len(server.ANSWERS) == 2315


def test_guess_returns_colors_status_and_remaining():
    gid = start("crane")
    data = guess(gid, "slate").json()
    assert data["pattern"] == "..G.G"
    assert data["colors"] == ["gray", "gray", "green", "gray", "green"]
    assert data["status"] == "playing"
    assert data["guesses_left"] == 5
    assert 1 <= data["remaining"] < 2315
    assert "answer" not in data  # don't leak it mid-game


def test_win_then_finished_game_errors():
    gid = start("crane")
    data = guess(gid, "crane").json()
    assert data["status"] == "won"
    assert data["answer"] == "crane"
    assert data["remaining"] == 1

    res = guess(gid, "slate")
    assert res.status_code == 409
    assert "over" in res.json()["detail"]
    assert client.get(f"/api/games/{gid}/hint").status_code == 409


def test_lose_reveals_answer():
    gid = start("crane")
    for _ in range(5):
        assert guess(gid, "dumpy").json()["status"] == "playing"
    data = guess(gid, "dumpy").json()
    assert data["status"] == "lost"
    assert data["answer"] == "crane"


@pytest.mark.parametrize(
    "word, message",
    [("cran", "5 letters"), ("crane1", "5 letters"), ("zzzzz", "not in the word list")],
)
def test_invalid_words(word, message):
    gid = start()
    res = guess(gid, word)
    assert res.status_code == 400
    assert message in res.json()["detail"]
    # A rejected guess doesn't use up a turn.
    assert guess(gid, "slate").json()["guesses_left"] == 5


def test_allowed_non_answer_word_is_accepted():
    gid = start()
    assert "aahed" not in server.ANSWERS
    assert guess(gid, "aahed").status_code == 200


def test_unknown_game_and_bad_body():
    assert guess("nope", "crane").status_code == 404
    assert client.get("/api/games/nope/hint").status_code == 404
    gid = start()
    assert client.post(f"/api/games/{gid}/guesses", json={}).status_code == 422


def test_hint_after_a_guess():
    gid = start("crane")
    remaining_after = guess(gid, "slate").json()["remaining"]
    data = client.get(f"/api/games/{gid}/hint?top=3").json()
    assert data["remaining"] == remaining_after
    entropies = [s["entropy"] for s in data["suggestions"]]
    assert len(entropies) == 3
    assert entropies == sorted(entropies, reverse=True)
    assert set(data["suggestions"][0]) == {"word", "entropy", "expected_remaining", "possible"}


def test_hint_top_is_validated():
    gid = start()
    assert client.get(f"/api/games/{gid}/hint?top=0").status_code == 422


def test_simulate(monkeypatch):
    # Full list takes ~40s; the endpoint shape is what's under test here.
    monkeypatch.setattr(server, "ANSWERS", ["crane", "crate", "crake", "crave"])
    server._simulation.cache_clear()
    try:
        data = client.get("/api/simulate").json()
    finally:
        server._simulation.cache_clear()
    assert data["games"] == 4
    assert sum(data["distribution"].values()) == 4
    assert data["failed"] == 0
    assert 1 <= data["average"] <= 4
