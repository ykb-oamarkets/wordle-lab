import random
from math import log2
from pathlib import Path

import pytest

from wordle.engine import load_words, score
from wordle.solver import entropy, remaining_words, simulate, solve, suggest

# All four share C R A _ E, so any one of them as a guess only says "it's me" or "it's not".
FOUR = ["crane", "crate", "crake", "crave"]
# TRANK separates all four: ".GGG.", "YGG..", ".GG.Y", ".GG.." respectively.
SPLITTER = "trank"


def test_remaining_words_keeps_only_consistent_words():
    history = [("crane", score("crane", "crave"))]  # GGG.G
    assert remaining_words(FOUR, history) == ["crate", "crake", "crave"]
    assert remaining_words(FOUR, []) == FOUR


def test_true_answer_is_never_filtered_out():
    answers = load_words(Path(__file__).parent.parent / "data" / "answers.txt")
    rng = random.Random(0)
    for _ in range(200):
        answer = rng.choice(answers)
        history = [(g, score(g, answer)) for g in rng.sample(answers, 3)]
        remaining = remaining_words(answers, history)
        assert answer in remaining
        assert all(score(g, w) == p for w in remaining for g, p in history)


def test_entropy():
    assert entropy(SPLITTER, FOUR) == pytest.approx(2.0)  # 4 equal groups of 1
    # One group of 1 (all green) and one of 3.
    assert entropy("crane", FOUR) == pytest.approx(-(0.25 * log2(0.25) + 0.75 * log2(0.75)))
    assert entropy("crane", ["crane"]) == 0


def test_suggest_ranks_by_entropy_even_if_word_cannot_win():
    top = suggest(FOUR, FOUR + [SPLITTER], top=2)
    assert top[0].word == SPLITTER
    assert top[0].entropy == pytest.approx(2.0)
    assert top[0].expected_remaining == pytest.approx(1.0)
    assert top[0].possible is False
    assert top[1].possible is True


def test_suggest_tie_break_prefers_a_possible_answer():
    # Both split {crane, crate} 1/1, but CRANE might win immediately.
    top = suggest(["crane", "crate"], [SPLITTER, "crane"], top=2)
    assert [s.word for s in top] == ["crane", SPLITTER]
    assert top[0].entropy == top[1].entropy == pytest.approx(1.0)


def test_suggest_with_one_word_left_picks_it():
    # Zero-information guesses that can't win are dropped, so only CRAVE is left.
    assert [s.word for s in suggest(["crave"], FOUR + [SPLITTER], top=5)] == ["crave"]


def test_solve_and_simulate():
    assert solve("crave", FOUR, FOUR + [SPLITTER]) == [SPLITTER, "crave"]
    assert simulate(FOUR, FOUR + [SPLITTER]) == {w: 2 for w in FOUR}
