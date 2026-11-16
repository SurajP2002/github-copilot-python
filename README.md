# Sudoku Web Game

A browser-based Sudoku game built with Flask and vanilla JavaScript. Choose a difficulty, solve puzzles with optional hints, track your time, and save your best results in a local leaderboard.

## Features

- **Three difficulties:** Easy (45 starting clues), Medium (35), and Hard (25). Generated puzzles are checked to have exactly one solution.
- **Interactive Sudoku board:** Immediate feedback for incorrect entries and rule conflicts. Original clues cannot be changed.
- **Check and Hint:** Check the current board or reveal and lock one correct value. Hints used are counted for each game.
- **Timer and completion:** The timer starts with a new game and stops when the puzzle is solved. The completion screen records time, difficulty, and hints used.
- **Top 10 leaderboard:** Enter a name after solving a puzzle. Scores are sorted by completion time and saved in browser `localStorage`.
- **Light and dark themes:** The selected theme is saved in browser `localStorage`.
- **Responsive interface:** Designed for desktop and mobile, with keyboard-visible focus styles and accessible status messages.

## Technologies

- Python 3 and Flask for the web application and Sudoku routes.
- HTML, CSS, and vanilla JavaScript for the interface and game interactions.
- Browser `localStorage` for leaderboard scores and theme preference.
- pytest for Python tests.
- Node.js built-in test runner for the JavaScript leaderboard and theme tests (optional).

## Project structure

```text
github-copilot-python/
├── .github/
├── .gitignore
├── CODEOWNERS
├── LICENSE.txt
├── README.md
└── starter/
    ├── app.py
    ├── requirements.txt
    ├── requirements-dev.txt
    ├── pytest.ini
    ├── sudoku/
    │   ├── __init__.py
    │   ├── logic.py
    │   └── routes.py
    ├── static/
    │   ├── main.js
    │   ├── styles.css
    │   ├── leaderboard.mjs
    │   └── theme.mjs
    ├── templates/
    │   └── index.html
    ├── tests/
    │   ├── test_app.py
    │   ├── test_sudoku_logic.py
    │   ├── leaderboard.test.mjs
    │   └── theme.test.mjs
    └── Screenshots/
```

`starter/app.py` runs the Flask application. The `sudoku` package keeps puzzle logic separate from Flask routes. Static browser assets are in `static/`, and the page template is in `templates/`.

## Installation and setup

### 1. Get the project

Clone the repository, then change into the application directory:

```powershell
git clone https://github.com/SurajP2002/github-copilot-python.git
cd github-copilot-python\starter
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If you use Windows Command Prompt instead, activate with:

```cmd
.venv\Scripts\activate.bat
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

From the `starter` directory, install the application dependencies:

```bash
python -m pip install -r requirements.txt
```

To install pytest as well, use the development requirements file. It includes the application requirements:

```bash
python -m pip install -r requirements-dev.txt
```

## Run the application

From the `starter` directory, with the virtual environment active:

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser. Stop the local server with **Ctrl+C** in the terminal.

## Run tests

Install the development dependencies if you have not already, then run pytest from the `starter` directory:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

The Python tests in `tests/test_app.py` cover the Flask routes and page, while `tests/test_sudoku_logic.py` tests the Sudoku logic.

Optional: if Node.js is installed, run the JavaScript tests for leaderboard and theme storage:

```bash
node --test tests/*.test.mjs
```

## Screenshots

The [`starter/Screenshots/`](starter/Screenshots/) folder contains screenshots of the application and its features, including the final game interface, mobile layout, light and dark themes, difficulty selector, hints, and leaderboard. For example:

- [Final game interface](starter/Screenshots/final_game_ui.png)
- [Mobile layout](starter/Screenshots/mobile_view.png)
- [Dark mode](starter/Screenshots/dark_mode.png)
- [Leaderboard](starter/Screenshots/leaderboard.png)
