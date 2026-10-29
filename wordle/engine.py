"""Wordle rules: scoring a guess, loading word lists, and tracking one game.

No web code here, so the CLI, the HTTP API and the tests all share it.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

WORD_LENGTH = 5
MAX_GUESSES = 6

# A pattern is a 5-char string: G = green, Y = yellow, . = gray. e.g. "..Y.G"
GREEN, YELLOW, GRAY = "G", "Y", "."
ALL_GREEN = GREEN * WORD_LENGTH


class WordleError(ValueError):
    """Base class for errors a player can cause."""


class InvalidGuess(WordleError):
    pass


class GameOver(WordleError):
    pass


def score(guess: str, answer: str) -> str:
    """Colour each letter of `guess` against `answer`.

    Two passes, so repeated letters are handled like real Wordle: greens claim
    their letters first, then yellows use up whatever copies are left.
    score("eerie", "crane") == "..Y.G"  (only one E in CRANE, and the green takes it)
    """
    result = [GRAY] * WORD_LENGTH
    unclaimed = {}  # answer letters not matched green -> how many copies remain
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            result[i] = GREEN
        else:
            unclaimed[a] = unclaimed.get(a, 0) + 1
    for i, g in enumerate(guess):
        if result[i] == GRAY and unclaimed.get(g, 0) > 0:
            result[i] = YELLOW
            unclaimed[g] -= 1
    return "".join(result)


def load_words(path: str | Path) -> List[str]:
    """Read one word per line; keep lowercase 5-letter alphabetic words, in order, deduplicated."""
    words = []
    seen = set()
    for line in Path(path).read_text().splitlines():
        w = line.strip().lower()
        if len(w) == WORD_LENGTH and w.isalpha() and w not in seen:
            seen.add(w)
            words.append(w)
    if not words:
        raise ValueError(f"no {WORD_LENGTH}-letter words found in {path}")
    return words


class Game:
    """One game: the hidden answer, the guesses so far, and win/lose status."""

    def __init__(self, answer: str, allowed: Iterable[str], max_guesses: int = MAX_GUESSES):
        self.allowed: Set[str] = set(allowed)
        self.answer = answer.lower()
        if self.answer not in self.allowed:
            raise ValueError(f"answer {answer!r} is not in the allowed words")
        self.max_guesses = max_guesses
        self.history: List[Tuple[str, str]] = []  # (guess, pattern)

    @classmethod
    def random(cls, answers: List[str], allowed: Iterable[str], rng: Optional[random.Random] = None) -> "Game":
        return cls((rng or random).choice(answers), allowed)

    @property
    def status(self) -> str:
        if self.history and self.history[-1][1] == ALL_GREEN:
            return "won"
        if len(self.history) >= self.max_guesses:
            return "lost"
        return "playing"

    @property
    def guesses_left(self) -> int:
        return self.max_guesses - len(self.history)

    def is_allowed(self, word: str) -> bool:
        return word.lower() in self.allowed

    def guess(self, word: str) -> str:
        """Score a guess and record it. Raises GameOver or InvalidGuess."""
        if self.status != "playing":
            raise GameOver(f"the game is over ({self.status})")
        word = word.strip().lower()
        if len(word) != WORD_LENGTH or not word.isalpha():
            raise InvalidGuess(f"guess must be {WORD_LENGTH} letters")
        if word not in self.allowed:
            raise InvalidGuess(f"{word.upper()!r} is not in the word list")
        pattern = score(word, self.answer)
        self.history.append((word, pattern))
        return pattern
