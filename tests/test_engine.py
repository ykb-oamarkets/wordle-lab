import pytest

from wordle.engine import Game, GameOver, InvalidGuess, load_words, score


@pytest.mark.parametrize(
    "guess, answer, expected",
    [
        ("crane", "crane", "GGGGG"),
        ("dumpy", "crane", "....."),
        # One E in the answer, already claimed by the green: earlier E's are gray, not yellow.
        ("eerie", "crane", "..Y.G"),
        # Two E's guessed, one in the answer, neither in place: first is yellow, second gray.
        ("speed", "abide", "..Y.Y"),
        # Green beats an earlier yellow for the same letter.
        ("geese", "these", "..GGG"),
        # Answer has two E's, guess has one.
        ("crane", "eerie", ".Y..G"),
        # Two different letters both yellow, alongside greens.
        ("babes", "abbey", "YYGG."),
    ],
)
def test_score(guess, answer, expected):
    assert score(guess, answer) == expected


ALLOWED = ["crane", "slate", "eerie", "abide", "speed", "dumpy", "these", "geese"]


def test_win():
    game = Game("crane", ALLOWED)
    assert game.guess("slate") == "..G.G"
    assert game.status == "playing"
    assert game.guess("CRANE") == "GGGGG"  # case-insensitive
    assert game.status == "won"
    assert game.guesses_left == 4


def test_lose_after_six():
    game = Game("crane", ALLOWED)
    for _ in range(6):
        game.guess("slate")
    assert game.status == "lost"
    with pytest.raises(GameOver):
        game.guess("crane")


def test_no_guesses_after_win():
    game = Game("crane", ALLOWED)
    game.guess("crane")
    with pytest.raises(GameOver):
        game.guess("slate")


@pytest.mark.parametrize("bad", ["cran", "cranes", "cr4ne", "", "zzzzz"])
def test_invalid_guess_is_rejected_and_not_counted(bad):
    game = Game("crane", ALLOWED)
    with pytest.raises(InvalidGuess):
        game.guess(bad)
    assert game.history == []


def test_answer_must_be_allowed():
    with pytest.raises(ValueError):
        Game("zzzzz", ALLOWED)


def test_load_words(tmp_path):
    f = tmp_path / "words.txt"
    f.write_text("Crane\n slate \ncrane\ntoolong\nab1de\n\nfour\n")
    assert load_words(f) == ["crane", "slate"]


def test_load_words_empty_file(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("nope\n")
    with pytest.raises(ValueError):
        load_words(f)
