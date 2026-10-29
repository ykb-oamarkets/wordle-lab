"""Terminal front end, using the same engine and solver as the web app.

    python -m wordle play        # play in the terminal; type ? for a hint
    python -m wordle simulate    # run the solver against every answer
"""
import sys
from collections import Counter
from pathlib import Path

from .engine import Game, WordleError, load_words
from .solver import remaining_words, simulate, suggest

DATA = Path(__file__).resolve().parent.parent / "data"
ANSWERS = load_words(DATA / "answers.txt")
ALLOWED = set(ANSWERS) | set(load_words(DATA / "allowed.txt"))


def play():
    game = Game.random(ANSWERS, ALLOWED)
    while game.status == "playing":
        try:
            word = input(f"guess {len(game.history) + 1}/{game.max_guesses} (? for hint): ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\nThe word was {game.answer}.")
            return
        if word == "?":
            remaining = remaining_words(ANSWERS, game.history)
            print(f"  {len(remaining)} words remaining")
            for s in suggest(remaining, ANSWERS):
                print(f"  {s.word}  {s.entropy:.2f} bits  ~{s.expected_remaining:.1f} left{'  (could win)' if s.possible else ''}")
            continue
        try:
            print("  " + game.guess(word))
        except WordleError as e:
            print(f"  {e}")
    print("You won!" if game.status == "won" else f"The word was {game.answer}.")


def run_simulation():
    print(f"Simulating {len(ANSWERS)} games (about 40s)...")
    results = simulate(ANSWERS, ANSWERS)
    counts = Counter(results.values())
    for n in sorted(counts):
        print(f"  {n}: {counts[n]:5d} {'#' * (counts[n] // 20)}")
    print(f"average {sum(results.values()) / len(results):.3f} guesses, failed (>6): {sum(c for n, c in counts.items() if n > 6)}")


if __name__ == "__main__":
    commands = {"play": play, "simulate": run_simulation}
    cmd = sys.argv[1] if len(sys.argv) > 1 else "play"
    if cmd not in commands:
        sys.exit(f"usage: python -m wordle [{'|'.join(commands)}]")
    commands[cmd]()
