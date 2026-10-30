"""Solver: which words are still possible, and which guess tells us the most.

The idea: a guess sorts the remaining words into groups by the colour pattern
it would show. The more evenly it splits them, the more we learn whatever the
pattern turns out to be. Entropy (in bits) measures that; each bit roughly
halves the remaining words.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from math import log2
from typing import Dict, Iterable, List, Sequence, Tuple

from .engine import ALL_GREEN, score


@dataclass(frozen=True)
class Suggestion:
    word: str
    entropy: float  # expected information in bits
    expected_remaining: float  # average words left after this guess
    possible: bool  # could this word itself be the answer?


def remaining_words(words: Iterable[str], history: Iterable[Tuple[str, str]]) -> List[str]:
    """Words consistent with every (guess, pattern) seen so far.

    A word survives if, had it been the answer, each past guess would have
    produced exactly the pattern we saw. Reuses `score`, so no separate rules.
    """
    history = list(history)
    return [w for w in words if all(score(g, w) == p for g, p in history)]


def split(guess: str, remaining: Sequence[str]) -> Dict[str, List[str]]:
    """Group the remaining words by the pattern `guess` would show against each one."""
    groups: Dict[str, List[str]] = {}
    for w in remaining:
        groups.setdefault(score(guess, w), []).append(w)
    return groups


def pattern_counts(guess: str, remaining: Sequence[str]) -> Counter:
    return Counter(score(guess, w) for w in remaining)


def entropy(guess: str, remaining: Sequence[str]) -> float:
    """H = -sum(p * log2 p) over the patterns `guess` would produce."""
    n = len(remaining)
    return -sum(c / n * log2(c / n) for c in pattern_counts(guess, remaining).values())


def suggest(remaining: Sequence[str], pool: Sequence[str], top: int = 5) -> List[Suggestion]:
    """Rank every word in `pool` as the next guess against `remaining`; return the best `top`."""
    return list(_rank(tuple(remaining), tuple(pool))[:top])


# ponytail: memoised on the exact remaining set. The opening (all answers remaining)
# costs ~7s once, after which games/simulations that reach the same position are free.
# Upgrade path if pools grow: precompute a guess x answer pattern table (numpy).
@lru_cache(maxsize=4096)
def _rank(remaining: Tuple[str, ...], pool: Tuple[str, ...]) -> Tuple[Suggestion, ...]:
    if not remaining:
        return ()
    n = len(remaining)
    candidates = set(remaining)
    ranked = []
    for guess in pool:
        counts = pattern_counts(guess, remaining).values()
        h = -sum(c / n * log2(c / n) for c in counts)
        possible = guess in candidates
        if h > 0 or possible:  # a guess that teaches nothing and can't win is never worth suggesting
            ranked.append(Suggestion(guess, h, sum(c * c for c in counts) / n, possible))
    # Best information first; on a tie prefer a word that could win outright.
    # Rounding stops float noise from beating the tie-break.
    ranked.sort(key=lambda s: (-round(s.entropy, 9), not s.possible, s.word))
    return tuple(ranked)


def solve(answer: str, words: Sequence[str], pool: Sequence[str]) -> List[str]:
    """Play the solver against `answer`, always taking the top suggestion. Returns the guesses made."""
    remaining = list(words)
    guesses = []
    while True:
        guess = suggest(remaining, pool, top=1)[0].word
        guesses.append(guess)
        pattern = score(guess, answer)
        if pattern == ALL_GREEN:
            return guesses
        remaining = [w for w in remaining if score(guess, w) == pattern]


def simulate(answers: Sequence[str], pool: Sequence[str]) -> Dict[str, int]:
    """Number of guesses the solver needs for every answer."""
    return {a: len(solve(a, answers, pool)) for a in answers}
