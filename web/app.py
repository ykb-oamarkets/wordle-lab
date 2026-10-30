"""HTTP API + static page. Thin layer: all game and solver logic lives in `wordle/`."""
from __future__ import annotations

import threading
import uuid
from collections import Counter
from contextlib import asynccontextmanager
from dataclasses import asdict
from functools import lru_cache
from math import log2
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from wordle.engine import MAX_GUESSES, Game, GameOver, InvalidGuess, load_words
from wordle.solver import entropy, remaining_words, simulate, split, suggest

ROOT = Path(__file__).resolve().parent.parent
ANSWERS = load_words(ROOT / "data" / "answers.txt")
ALLOWED = set(ANSWERS) | set(load_words(ROOT / "data" / "allowed.txt"))
COLORS = {"G": "green", "Y": "yellow", ".": "gray"}

# ponytail: in-memory store, games vanish on restart (no DB needed)
games: Dict[str, Game] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The opening hint ranks 2315 x 2315 pairs (~7s); warm the cache so the first click is instant.
    threading.Thread(target=suggest, args=(ANSWERS, ANSWERS), daemon=True).start()
    yield


app = FastAPI(title="Wordle Lab", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


class GuessIn(BaseModel):
    guess: str


def get_game(game_id: str) -> Game:
    game = games.get(game_id)
    if game is None:
        raise HTTPException(404, f"no game with id {game_id!r}; start a new one")
    return game


def get_playing_game(game_id: str) -> Game:
    game = get_game(game_id)
    if game.status != "playing":
        raise HTTPException(409, f"the game is over ({game.status}); start a new one")
    return game


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/api/games", status_code=201)
def new_game():
    game = Game.random(ANSWERS, ALLOWED)
    game_id = uuid.uuid4().hex
    games[game_id] = game
    return {"id": game_id, "max_guesses": MAX_GUESSES, "remaining": len(ANSWERS)}


@app.get("/api/words")
def words():
    """Every possible secret word, in a fixed order, so the page can draw the pile."""
    return {"words": ANSWERS}


@app.post("/api/games/{game_id}/guesses")
def make_guess(game_id: str, body: GuessIn):
    game = get_game(game_id)
    try:
        pattern = game.guess(body.guess)
    except GameOver as e:
        raise HTTPException(409, str(e))
    except InvalidGuess as e:
        raise HTTPException(400, str(e))
    remaining = remaining_words(ANSWERS, game.history)
    out = {
        "guess": game.history[-1][0],
        "pattern": pattern,
        "colors": [COLORS[c] for c in pattern],
        "status": game.status,
        "guesses_left": game.guesses_left,
        "remaining": len(remaining),
        "remaining_words": remaining,  # only uses colors already shown, so no spoiler
    }
    if game.status != "playing":
        out["answer"] = game.answer
    return out


@app.get("/api/games/{game_id}/hint")
def hint(game_id: str, top: int = Query(5, ge=1, le=20)):
    game = get_playing_game(game_id)
    remaining = remaining_words(ANSWERS, game.history)
    return {
        "remaining": len(remaining),
        "remaining_words": remaining if len(remaining) <= 20 else None,
        "suggestions": [asdict(s) for s in suggest(remaining, ANSWERS, top)],
    }


@app.get("/api/games/{game_id}/split")
def split_preview(game_id: str, guess: str):
    """What-if: how `guess` would split the remaining words, before you commit to it."""
    game = get_playing_game(game_id)
    word = guess.strip().lower()
    if not game.is_allowed(word):
        raise HTTPException(400, f"{word.upper()!r} is not in the word list")
    remaining = remaining_words(ANSWERS, game.history)
    groups = sorted(split(word, remaining).items(), key=lambda kv: (-len(kv[1]), kv[0]))
    best = suggest(remaining, ANSWERS, top=1)[0]
    return {
        "guess": word,
        "remaining": len(remaining),
        "entropy": entropy(word, remaining),
        "max_entropy": log2(min(len(remaining), 3 ** 5)),  # every word in its own group
        "expected_remaining": sum(len(ws) ** 2 for _, ws in groups) / len(remaining),
        "possible": word in remaining,
        "best": asdict(best),
        "groups": [{"pattern": p, "colors": [COLORS[c] for c in p], "words": ws} for p, ws in groups],
    }


@app.get("/api/simulate")
def run_simulation():
    return _simulation()


# ponytail: full run takes ~40s, so compute once per process and cache.
@lru_cache(maxsize=1)
def _simulation():
    results = simulate(ANSWERS, ANSWERS)
    counts = Counter(results.values())
    hardest = sorted(results.items(), key=lambda kv: -kv[1])[:10]
    return {
        "games": len(results),
        "average": round(sum(results.values()) / len(results), 4),
        "distribution": {n: counts[n] for n in sorted(counts)},
        "failed": sum(c for n, c in counts.items() if n > MAX_GUESSES),
        "hardest": [{"answer": a, "guesses": n} for a, n in hardest],
    }
