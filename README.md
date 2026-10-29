<a id="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <h3 align="center">Wordle Lab</h3>

  <p align="center">
    Play Wordle in your browser. When you're stuck, a solver tells you the best next guess and shows the maths behind it.
    <br />
    <a href="#how-it-works"><strong>See how it works »</strong></a>
    <br />
    <br />
    <a href="#usage">Run it</a>
    &middot;
    <a href="#api">API</a>
    &middot;
    <a href="#how-this-was-built-and-checked">How this was built and checked</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About the project</a>
      <ul>
        <li><a href="#how-it-works">How it works</a></li>
        <li><a href="#built-with">Built with</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
      <ul>
        <li><a href="#play-in-the-browser">Play in the browser</a></li>
        <li><a href="#play-in-the-terminal">Play in the terminal</a></li>
        <li><a href="#api">API</a></li>
        <li><a href="#project-layout">Project layout</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#how-this-was-built-and-checked">How this was built and checked</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About the project

![Wordle Lab mid-game, with the hint panel open][product-screenshot]

Wordle hides a five-letter word and gives you six guesses. After each guess, every letter changes color:

* Green means right letter, right spot.
* Yellow means the letter is in the word, but somewhere else.
* Gray means the letter isn't in the word, or the word has no copies of it left.

Wordle Lab is that game with a helper sitting next to you. The helper keeps a pile of every word that could still be the answer. Ask it for a hint and it tells you which guess would shrink that pile the most.

I built it as a take-home exercise. The brief asked for four parts and one optional extra. All five are here:

1. A game engine that colors guesses and knows when you've won or lost.
2. A solver that works out which words are still possible and ranks the next guesses.
3. An HTTP API to start a game, make a guess and ask for a hint.
4. A web page with a board, a keyboard, a hint panel and a words-remaining counter.
5. A simulate button that plays every possible answer and charts how many guesses each one took.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### How it works

#### Coloring a guess

Repeated letters are the hard part. The engine makes two passes over your guess. The first pass marks the greens. The second pass goes through the other letters and makes one yellow only if the answer still has an unused copy of it.

Say the answer is CRANE and you guess EERIE. The last E is green, and it uses up the only E in CRANE. So the first two E's turn gray, not yellow. A quick "is this letter anywhere in the word?" check gets this wrong, and the tests cover it.

#### Shrinking the pile

Picture every possible answer written on its own card. After each guess, the solver picks up each card and asks one question. If this card were the answer, would my guess have shown exactly these colors? If not, the card goes in the bin.

To answer that question, the solver calls the same coloring code the game uses. That means the solver and the game can't disagree about the rules. The number of cards left is the "words remaining" counter on the page.

#### Picking the best guess

Think about 20 Questions. "Is it a giraffe?" is a bad question. The answer is nearly always no, and you've learned almost nothing. "Is it bigger than a cat?" is a good one, because either answer rules out about half the options.

The solver judges every guess the same way. It pretends to play the guess against each card in the pile and sorts the cards into groups by the colors that would come back. If the cards land in lots of small groups, the guess is good, because whatever colors you see, only a few words survive. If they all land in one group, the guess tells you nothing.

Entropy turns that spread into a single number, measured in bits. Each bit roughly halves the pile. With 8 words left, a guess that gives each word its own color pattern is worth 3 bits, because 8 halves to 4, then 2, then 1. A guess that gives all 8 the same pattern is worth 0. The formula is `H = -Σ p·log₂(p)`, where `p` is the share of the pile in each group.

Each hint shows three things per word:

* Bits, the entropy described above.
* Avg left, the number of words you can expect to still have after guessing it.
* A "could win" tag if the word might be the answer itself.

Sometimes the best guess can't win. After RAISE, the top hint is often a word like COUNT that has none of the letters you already found. It looks odd, but it tests five new letters at once. When two guesses tie, the solver picks the one that could win. It never suggests a word that teaches nothing and can't win.

#### How well it plays

The solver opens with RAISE, worth 5.88 bits. I ran it against all 2,315 answers. It averages 3.50 guesses and never needs more than six.

| Guesses needed | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Games | 1 | 61 | 1,139 | 1,020 | 92 | 2 |

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built with

* [![Python][Python-badge]][Python-url]
* [![FastAPI][FastAPI-badge]][FastAPI-url]
* [![pytest][pytest-badge]][pytest-url]
* [![JavaScript][JavaScript-badge]][JavaScript-url]

The page is one HTML file with plain JavaScript. There's no build step and no front-end framework.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting started

### Prerequisites

You need Python 3.9 or newer. Check what you have with:

```sh
python3 --version
```

The word lists ship in `data/`, so there's nothing else to download.

### Installation

1. Unzip the folder or clone the repo, then move into it.
   ```sh
   cd wordle-lab
   ```
2. Make a virtual environment and switch it on.
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install the packages.
   ```sh
   pip install -r requirements.txt
   ```
4. Run the tests. All 38 should pass in about two seconds.
   ```sh
   python -m pytest
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

### Play in the browser

```sh
python -m uvicorn web.app:app --port 8000
```

Open http://localhost:8000. Type on your keyboard or click the keys on screen. Press **Get hint** when you want help. Click any suggested word to type it in. After your first hint, the panel refreshes on its own after every guess.

The first hint of a game compares 2,315 words against 2,315 words, which takes about seven seconds. The server starts that work the moment it boots, so the result is usually ready before you ask.

**Simulate all answers** takes about 40 seconds the first time. The server keeps the result, so later clicks show it straight away.

### Play in the terminal

```sh
python -m wordle play        # type ? for a hint
python -m wordle simulate    # solver vs. every answer, about 40 seconds
```

The terminal version imports the same engine and solver as the website and has no web code at all. The brief asked for the game logic to work no matter how it's used, and this is the proof.

### API

| Method | Path | What you get back |
|---|---|---|
| `POST` | `/api/games` | A new game's `id`, `max_guesses` and `remaining` |
| `POST` | `/api/games/{id}/guesses` with `{"guess": "crane"}` | `pattern`, `colors`, `status`, `guesses_left`, `remaining`, plus `answer` once the game ends |
| `GET` | `/api/games/{id}/hint?top=5` | `remaining`, the top `suggestions` with `entropy`, `expected_remaining` and `possible`, and `remaining_words` when 20 or fewer are left |
| `GET` | `/api/simulate` | `games`, `average`, `distribution`, `failed` and the 10 `hardest` answers |

Patterns use `G` for green, `Y` for yellow and `.` for gray, so CRANE against EERIE comes back as `..Y.G`.

Every error comes back as `{"detail": "<message>"}`:

* `400` means the guess was the wrong length, had non-letters, or isn't in the word list. It doesn't cost you a turn.
* `404` means there's no game with that id. Games live in memory, so restarting the server clears them.
* `409` means the game is already over, for both guesses and hints.
* `422` means the request body was missing or malformed, or `top` was outside 1 to 20.

The hint only uses the colors you've already seen. It never looks at the hidden answer.

### Project layout

```
wordle/            game logic, no web code
  engine.py        score(), load_words(), Game
  solver.py        remaining_words(), entropy(), suggest(), solve(), simulate()
  __main__.py      terminal version
web/
  app.py           FastAPI routes that call into wordle/
  index.html       the page
data/
  answers.txt      2,315 words that can be the answer
  allowed.txt      10,657 more words you're allowed to guess
tests/             engine, solver and API tests
```

`web/` imports from `wordle/`. Nothing in `wordle/` imports from `web/`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [x] Game engine that handles repeated letters correctly
- [x] Entropy solver with ranked hints
- [x] HTTP API with clear error messages
- [x] Web page with board, keyboard, hint panel and counter
- [x] Simulate every answer
- [ ] Let the solver suggest any of the 12,972 allowed words, not just the 2,315 answers. Guesses would get slightly better, but each hint would take about five times longer.
- [ ] Precompute every guess-by-answer pattern once with numpy, to bring the simulation down from 40 seconds to a few.
- [ ] Save games to disk so a restart doesn't wipe them. The brief said no database, so they live in memory for now.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- AI USAGE -->
## How this was built and checked

<!-- Rewrite this section in your own words before you submit. -->

The brief asks which parts an AI tool wrote and how they were checked. I used Claude Code to write the code. I didn't take the output on trust. These are the checks:

* I worked out the coloring tests by hand, one for each repeated-letter trap. Those cover a green using up the only copy, two guessed copies against one in the answer, and one guessed copy against two in the answer.
* A randomized test plays 200 games and confirms the true answer never gets thrown out of the pile. It also confirms every word left in the pile matches the colors seen so far.
* The entropy tests use four words, CRANE, CRATE, CRAKE and CRAVE, small enough to check on paper. A guess that splits them perfectly scores exactly 2 bits. A guess that splits them one and three scores 0.811 bits.
* The full simulation solves all 2,315 answers. Every game ends on five greens, and none takes more than six guesses.
* I drove the page in a real browser. I typed a fake word, played a full game using only the hints, ran the simulation, and stopped the server mid-game to make sure the page showed an error and kept working.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
