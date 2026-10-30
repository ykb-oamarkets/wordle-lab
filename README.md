<a id="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <h3 align="center">Wordle Lab</h3>

  <p align="center">
    Play Wordle in your browser. Stuck? Ask for a hint and the solver shows you the best next guess, and why.
    <br />
    <a href="#how-it-works"><strong>See how it works »</strong></a>
    <br />
    <br />
    <a href="#usage">Run it</a>
    &middot;
    <a href="#api">API</a>
    &middot;
    <a href="#how-i-built-and-checked-it">How I built and checked it</a>
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
    <li><a href="#how-i-built-and-checked-it">How I built and checked it</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About the project

![Wordle Lab mid-game: the solver measures CLOUT and lights up its words in the pile][product-screenshot]

Wordle hides a secret five-letter word. You get six guesses. After each guess, every letter changes color:

* Green means right letter, right spot.
* Yellow means the letter is in the word, but somewhere else.
* Gray means the letter isn't in the word, or the word has no copies of it left.

Wordle Lab is that game with a solver built in. Think of the solver as a friend sitting next to you. It keeps a pile of every word that could still be the secret. Ask it for a hint and it tells you which guess would shrink that pile the most.

Here's what's inside:

1. The game. It colors your guesses and knows when you've won or lost.
2. The solver. It throws out words that can't be the secret and ranks your next guesses.
3. An HTTP API, so any program can start a game, guess and ask for hints.
4. A web page with a board, a keyboard, a hint panel and a words-remaining counter.
5. A simulate button. The solver plays every possible secret word and charts how many guesses each one took.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### How it works

#### Coloring a guess

The game checks your guess in two rounds.

Round one finds the greens. Round two looks at the letters left over. A letter only turns yellow if the secret word still has a spare copy of it.

Here's why that matters. The secret is CRANE and you guess EERIE. CRANE has just one E. The last E in EERIE is green, so it takes that one E. There's no E left to spare, so the first two E's turn gray, not yellow.

#### Throwing out words

Picture every possible secret word written on its own card.

After each guess, the solver picks up each card and asks, "If this were the secret, would I have seen these exact colors?" If the answer is no, the card goes in the bin. The cards left over are the "words remaining" number on the page.

The solver uses the same coloring code as the game to answer that question. So the two always agree on the rules.

#### Picking the best guess

Start with a toy game. Your friend hides one of 8 toys behind their back, and you get to ask questions.

"Is it the purple dinosaur?" is a bad question. The answer is almost always no, and you still have 7 toys to choose from.

"Is it an animal?" is a good question if 4 of the toys are animals. Whatever the answer, half the toys are gone.

Entropy counts how many times a question cuts the pile in half. Each halving is one bit.

| The pile goes from | Halvings | Entropy |
|---|---|---|
| 8 to 8 | none | 0 bits, useless |
| 8 to 4 | once | 1 bit |
| 8 to 2 | twice | 2 bits |
| 8 to 1 | three times | 3 bits, you know the secret |

In Wordle, your guess is the question and the colors are the answer. Say only 4 words are left: CRANE, CRATE, CRAVE and CRAZE.

* **Guess CRATE.** If the secret is CRATE, you see all green. If it's any of the other three, you see the same colors every time. So most of the time you still have 3 words left. That's worth about 0.8 bits.
* **Guess EVENT.** Each of the 4 words gives back different colors. Whatever you see, you know the secret. Going from 4 to 1 is two halvings, so it's worth 2 bits. EVENT can't win, but it's the better guess.

The solver does this for every word it could guess. It pretends each remaining word is the secret, puts words that would give the same colors into the same group, and scores how small the groups are. Then it suggests the words with the most bits.

Even groups beat uneven ones. With 4 words, a 2-and-2 split always leaves you with 2. A 1-and-3 split usually leaves you with 3. The formula `H = -Σ p·log₂(p)` gives the score, where `p` is the share of words that land in each group.

#### Reading a hint

Each row in the hint panel shows:

* Bits, how many times the guess should halve the pile.
* Avg left, about how many words you'll still have after guessing it.
* A "could win" tag, if the word might be the secret itself.

After RAISE, the top hint is often a word like COUNT that can't be the secret. That looks strange, but COUNT tests five new letters at once. When two words tie on bits, the solver picks the one that could win.

#### How well it plays

The solver always opens with RAISE, worth 5.88 bits. I had it play all 2,315 possible secret words. It needs 3.50 guesses on average and never more than six.

| Guesses needed | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Games | 1 | 61 | 1,139 | 1,020 | 92 | 2 |

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built with

* [![Python][Python-badge]][Python-url]
* [![FastAPI][FastAPI-badge]][FastAPI-url]
* [![pytest][pytest-badge]][pytest-url]
* [![JavaScript][JavaScript-badge]][JavaScript-url]
* [![GSAP][GSAP-badge]][GSAP-url]

The page is one HTML file with plain JavaScript. There's no build step and no front-end framework. GSAP runs the animations, and a copy ships in `web/static/`, so it works offline. The typeface is Gabarito from Google Fonts. Offline, the page falls back to a system font.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting started

### Prerequisites

You need Python 3.9 or newer. Check what you have with:

```sh
python3 --version
```

The word lists are already in `data/`, so there's nothing else to download.

### Installation

1. Clone the repo and move into it.
   ```sh
   git clone https://github.com/ykb-oamarkets/wordle-lab.git
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
4. Run the tests. All 42 should pass in about two seconds.
   ```sh
   python -m pytest
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Run every command below from the `wordle-lab` folder with the virtual environment switched on. If you see `command not found: python`, run `source .venv/bin/activate` first. Each new terminal tab needs it again.

### Play in the browser

```sh
python -m uvicorn web.app:app --port 8000
```

Open http://localhost:8000. Everything fits on one screen, so there's nothing to scroll. You play on the left. On the right, a little blue solver talks you through what's happening, like "RAISE knocked out 2,306 words. 9 left."

* **The pile.** Every possible secret word is one dot. After each guess, the ruled-out dots wink out and the number counts down. When 12 or fewer are left, their names show up underneath.
* **Measure your guess.** Type five letters and stop before you press Enter. You'll see how many bits the guess is worth, a grade from Weak to Best possible, and the solver's own pick if it has a better one. Below that is a row of blocks, one for each group of words the guess would make. Many small blocks means a great guess. Point at a block and its words light up blue in the pile.
* **My picks.** Press `?` or click **Show me**. Click a pick to type it, and the meter measures it. A green dot means the word could be the secret. After your first ask, the picks update by themselves after every guess.

The first measurement of a game checks 2,315 words against 2,315 words, which takes about seven seconds. The server starts on it as soon as it boots, so it's usually ready before you ask.

**Benchmark** opens a pop-up where the solver plays every secret word. It takes about 40 seconds the first time. The server remembers the result, so later clicks show it straight away.

### Play in the terminal

```sh
python -m wordle play        # type ? for a hint
python -m wordle simulate    # the solver plays every secret word, about 40 seconds
```

The terminal version uses the same game and solver as the website, with no web code at all. The game logic doesn't depend on the website.

### API

| Method | Path | What you get back |
|---|---|---|
| `POST` | `/api/games` | A new game's `id`, `max_guesses` and `remaining` |
| `GET` | `/api/words` | Every possible secret word, in the order the pile draws them |
| `POST` | `/api/games/{id}/guesses` with `{"guess": "crane"}` | `pattern`, `colors`, `status`, `guesses_left`, `remaining`, `remaining_words`, plus `answer` once the game ends |
| `GET` | `/api/games/{id}/hint?top=5` | `remaining`, the top `suggestions` with `entropy`, `expected_remaining` and `possible`, and `remaining_words` when 20 or fewer are left |
| `GET` | `/api/games/{id}/split?guess=crane` | What would happen if you guessed this word: `entropy`, `max_entropy`, `expected_remaining`, `possible`, the solver's `best` guess, and the `groups` of words for each color pattern. It doesn't use up a turn. |
| `GET` | `/api/simulate` | `games`, `average`, `distribution`, `failed` and the 10 `hardest` secret words |

Patterns use `G` for green, `Y` for yellow and `.` for gray. CRANE against EERIE comes back as `..Y.G`.

Every error comes back as `{"detail": "<message>"}`:

* `400` means the guess was the wrong length, had non-letters, or isn't in the word list. It doesn't cost you a turn.
* `404` means there's no game with that id. Games live in memory, so restarting the server clears them.
* `409` means the game is already over, for guesses, hints and previews.
* `422` means the request body was missing or broken, or `top` was outside 1 to 20.

Hints only use the colors you've already seen. They never peek at the secret word.

### Project layout

```
wordle/            game logic, no web code
  engine.py        score(), load_words(), Game
  solver.py        remaining_words(), split(), entropy(), suggest(), solve(), simulate()
  __main__.py      terminal version
web/
  app.py           FastAPI routes that call into wordle/
  index.html       the page
data/
  answers.txt      2,315 words that can be the secret
  allowed.txt      10,657 more words you're allowed to guess
tests/             game, solver and API tests
```

`web/` imports from `wordle/`. Nothing in `wordle/` imports from `web/`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [x] Game that handles repeated letters correctly
- [x] Entropy solver with ranked hints
- [x] HTTP API with clear error messages
- [x] Web page with board, keyboard, hint panel and counter
- [x] Simulate every secret word
- [ ] Let the solver suggest any of the 12,972 allowed words, not just the 2,315 possible secrets. Guesses would get a little better, but each hint would take about five times longer.
- [ ] Work out every guess-and-secret color pattern once with numpy, so the simulation takes a few seconds instead of 40.
- [ ] Save games to disk so a restart doesn't wipe them. Right now they only live in memory.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- AI USAGE -->
## How I built and checked it

I built this with Claude Code, an AI coding tool. Code that runs isn't the same as code that's right, so here's what checks it:

* There's a test for each repeated-letter trap, and every expected color was worked out by hand. The traps are a green using up the only copy, two guessed copies against one in the secret word, and one guessed copy against two.
* A random test plays 200 games. It checks that the real secret word never gets thrown out, and that every word left matches the colors seen so far.
* The entropy tests use CRANE, CRATE, CRAVE and CRAZE from the example above, because they're small enough to check on paper. EVENT scores exactly 2 bits. Guessing one of the four words scores 0.811.
* The simulation plays all 2,315 secret words. Every game ends on five greens, and none takes more than six guesses.
* A run in a real browser typed a fake word, played a full game using only hints, ran the simulation, and stopped the server mid-game. The page showed an error message and kept working.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
[product-screenshot]: images/wordle-lab.png
[Python-badge]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[FastAPI-badge]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[FastAPI-url]: https://fastapi.tiangolo.com/
[pytest-badge]: https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white
[pytest-url]: https://docs.pytest.org/
[JavaScript-badge]: https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black
[JavaScript-url]: https://developer.mozilla.org/en-US/docs/Web/JavaScript
[GSAP-badge]: https://img.shields.io/badge/GSAP-0AE448?style=for-the-badge&logo=greensock&logoColor=black
[GSAP-url]: https://gsap.com/
