// Client-side rendering and interaction for the Flask-backed Sudoku
import {
  addLeaderboardScore,
  normalizePlayerName,
  readLeaderboard,
  writeLeaderboard
} from './leaderboard.mjs';
import {readTheme, writeTheme} from './theme.mjs';

const SIZE = 9;
let currentTheme = 'light';
let puzzle = [];
let timerInterval = null;
let elapsedSeconds = 0;
let validationRequestId = 0;
let newGameRequestId = 0;
let hintRequestId = 0;
let hintsUsed = 0;
let currentDifficulty = 'medium';
let completionRecord = null;
let scoreSavedForGame = false;

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
  const seconds = (totalSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function updateTimer() {
  document.getElementById('timer').innerText = formatTime(elapsedSeconds);
}

function showMessage(text, type = 'error') {
  const message = document.getElementById('message');
  message.innerText = text;
  message.classList.toggle('success', type === 'success');
  message.classList.toggle('error', type === 'error');
}

function clearMessage() {
  showMessage('', '');
}

function setThemeStatus(text, isError = false) {
  const status = document.getElementById('theme-status');
  status.innerText = text;
  status.classList.toggle('error', isError);
}

function applyTheme(theme) {
  currentTheme = theme;
  document.documentElement.dataset.theme = theme;
  const toggle = document.getElementById('theme-toggle');
  toggle.setAttribute('aria-pressed', String(theme === 'dark'));
  toggle.innerText = `Dark Mode: ${theme === 'dark' ? 'On' : 'Off'}`;
}

function initializeTheme() {
  try {
    applyTheme(readTheme(window.localStorage));
  } catch {
    applyTheme('light');
    setThemeStatus('Theme preference could not be loaded; using Light Mode.', true);
  }
}

function toggleTheme() {
  const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
  applyTheme(nextTheme);

  try {
    writeTheme(window.localStorage, nextTheme);
    setThemeStatus(`${nextTheme === 'dark' ? 'Dark' : 'Light'} Mode enabled.`);
  } catch {
    setThemeStatus('Theme changed for this session but could not be saved.', true);
  }
}

function stopTimer() {
  if (timerInterval !== null) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function resetTimer() {
  stopTimer();
  elapsedSeconds = 0;
  updateTimer();
}

function startTimer() {
  stopTimer();
  timerInterval = setInterval(() => {
    elapsedSeconds += 1;
    updateTimer();
  }, 1000);
}

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';
  for (let i = 0; i < SIZE; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    for (let j = 0; j < SIZE; j++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = 1;
      input.className = 'sudoku-cell';
      input.dataset.row = i;
      input.dataset.col = j;
      input.addEventListener('input', (e) => {
        const val = e.target.value.replace(/[^1-9]/g, '');
        e.target.value = val;
      });
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function renderPuzzle(puz) {
  puzzle = puz;
  createBoardElement();
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = puzzle[i][j];
      const inp = inputs[idx];
      if (val !== 0) {
        inp.value = val;
        inp.disabled = true;
        inp.className += ' prefilled';
      } else {
        inp.value = '';
        inp.disabled = false;
      }
    }
  }
}

function readBoard() {
  const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');
  const board = [];
  for (let row = 0; row < SIZE; row++) {
    board[row] = [];
    for (let col = 0; col < SIZE; col++) {
      const value = inputs[row * SIZE + col].value;
      board[row][col] = value ? parseInt(value, 10) : 0;
    }
  }
  return board;
}

function applyFeedback(incorrectCells, conflictingCells) {
  const incorrect = new Set(incorrectCells.map(([row, col]) => row * SIZE + col));
  const conflicting = new Set(conflictingCells.map(([row, col]) => row * SIZE + col));
  const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');

  for (let index = 0; index < inputs.length; index++) {
    inputs[index].classList.toggle('incorrect', incorrect.has(index));
    inputs[index].classList.toggle('conflicting', conflicting.has(index));
  }
}

function completeGame() {
  if (completionRecord !== null) return;

  stopTimer();
  validationRequestId++;
  hintRequestId++;
  scoreSavedForGame = false;
  completionRecord = {
    timeSeconds: elapsedSeconds,
    time: formatTime(elapsedSeconds),
    difficulty: currentDifficulty,
    hintsUsed
  };

  const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');
  for (const input of inputs) {
    input.disabled = true;
  }
  document.getElementById('use-hint').disabled = true;
  document.getElementById('check-solution').disabled = true;

  const hintText = hintsUsed === 1 ? 'hint' : 'hints';
  showMessage(
    `Congratulations! You solved it in ${completionRecord.time}. ` +
    `Difficulty: ${completionRecord.difficulty}. ` +
    `Hints used: ${completionRecord.hintsUsed} ${hintText}.`,
    'success'
  );
  setLeaderboardStatus('');
  document.getElementById('player-name-dialog').showModal();
  document.getElementById('player-name').focus();
}

function setLeaderboardStatus(text, isError = false) {
  const status = document.getElementById('leaderboard-status');
  status.innerText = text;
  status.classList.toggle('error', isError);
}

function renderLeaderboard(scores, emptyText = 'No scores yet.') {
  const entries = document.getElementById('leaderboard-entries');
  entries.innerHTML = '';

  if (scores.length === 0) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 4;
    cell.innerText = emptyText;
    row.appendChild(cell);
    entries.appendChild(row);
    return;
  }

  for (const score of scores) {
    const row = document.createElement('tr');
    const values = [
      score.name,
      formatTime(score.timeSeconds),
      score.difficulty,
      score.hintsUsed
    ];
    for (const value of values) {
      const cell = document.createElement('td');
      cell.innerText = value;
      row.appendChild(cell);
    }
    entries.appendChild(row);
  }
}

function loadLeaderboard() {
  try {
    renderLeaderboard(readLeaderboard(window.localStorage));
  } catch {
    renderLeaderboard([], 'Leaderboard unavailable.');
    setLeaderboardStatus(
      'Unable to load the leaderboard. Saved data may be invalid or browser storage unavailable.',
      true
    );
  }
}

function savePlayerScore(event) {
  event.preventDefault();
  const nameInput = document.getElementById('player-name');
  const nameError = document.getElementById('player-name-error');
  const name = normalizePlayerName(nameInput.value);
  if (name === null) {
    nameError.innerText = 'Enter a name between 1 and 40 characters.';
    nameInput.setAttribute('aria-invalid', 'true');
    nameInput.focus();
    return;
  }

  nameInput.removeAttribute('aria-invalid');
  nameError.innerText = '';
  const score = {
    name,
    timeSeconds: completionRecord.timeSeconds,
    difficulty: completionRecord.difficulty,
    hintsUsed: completionRecord.hintsUsed
  };

  try {
    const scores = readLeaderboard(window.localStorage);
    const updatedScores = addLeaderboardScore(scores, score);
    renderLeaderboard(writeLeaderboard(window.localStorage, updatedScores));
    scoreSavedForGame = true;
    setLeaderboardStatus('Score saved to the leaderboard.');
    document.getElementById('player-name-dialog').close();
  } catch {
    setLeaderboardStatus(
      'Unable to save the score. Check browser storage and try again.',
      true
    );
  }
}

async function validateBoard() {
  const requestId = ++validationRequestId;
  const res = await fetch('/validate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board: readBoard()})
  });
  const data = await res.json();
  if (requestId !== validationRequestId) return;
  if (!res.ok) {
    showMessage(data.error);
    return;
  }
  applyFeedback(data.incorrect, data.conflicts);
  if (data.solved) completeGame();
}

async function newGame() {
  const requestId = ++newGameRequestId;
  validationRequestId++;
  hintRequestId++;
  const hintButton = document.getElementById('use-hint');
  hintButton.disabled = true;
  hintsUsed = 0;
  document.getElementById('hints-used').innerText = hintsUsed;
  resetTimer();
  const difficulty = document.getElementById('difficulty').value;
  const res = await fetch(`/new?difficulty=${encodeURIComponent(difficulty)}`);
  const data = await res.json();
  if (requestId !== newGameRequestId) return;
  if (!res.ok) {
    hintButton.disabled = false;
    showMessage(data.error);
    return;
  }
  validationRequestId++;
  hintRequestId++;
  renderPuzzle(data.puzzle);
  completionRecord = null;
  document.getElementById('check-solution').disabled = false;
  const difficultyLabel = {
    easy: 'Easy',
    medium: 'Medium',
    hard: 'Hard'
  }[difficulty];
  currentDifficulty = difficultyLabel;
  document.getElementById('current-difficulty').innerText =
    `Current difficulty: ${difficultyLabel}`;
  clearMessage();
  hintButton.disabled = false;
  startTimer();
}

async function useHint() {
  const hintButton = document.getElementById('use-hint');
  if (hintButton.disabled) return;

  const requestId = ++hintRequestId;
  hintButton.disabled = true;
  try {
    const res = await fetch('/hint', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({board: readBoard()})
    });
    const data = await res.json();
    if (requestId !== hintRequestId) return;
    if (!res.ok) {
      showMessage(data.error);
      return;
    }

    const index = data.row * SIZE + data.col;
    const input = document.getElementById('sudoku-board').getElementsByTagName('input')[index];
    if (input.disabled || input.value !== '') {
      showMessage('That cell changed before the hint arrived. Try again.');
      return;
    }

    input.value = data.value;
    input.disabled = true;
    input.classList.add('hinted');
    hintsUsed += 1;
    document.getElementById('hints-used').innerText = hintsUsed;
    clearMessage();
    validateBoard();
  } finally {
    if (requestId === hintRequestId) hintButton.disabled = false;
  }
}

async function checkSolution() {
  const requestId = ++validationRequestId;
  const res = await fetch('/check', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board: readBoard()})
  });
  const data = await res.json();
  if (requestId !== validationRequestId) return;
  if (data.error) {
    showMessage(data.error);
    return;
  }
  const incorrect = new Set(data.incorrect.map(x => x[0]*SIZE + x[1]));
  applyFeedback(data.incorrect, data.conflicts);
  if (data.solved) {
    completeGame();
  } else if (incorrect.size === 0 && data.conflicts.length === 0) {
    showMessage('The puzzle is incomplete.');
  } else {
    showMessage('Some cells are incorrect.');
  }
}

// Wire buttons
window.addEventListener('load', () => {
  initializeTheme();
  document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
  loadLeaderboard();
  document.getElementById('player-name-form').addEventListener('submit', savePlayerScore);
  document.getElementById('skip-score').addEventListener('click', () => {
    document.getElementById('player-name-dialog').close();
  });
  document.getElementById('player-name-dialog').addEventListener('close', () => {
    if (!scoreSavedForGame) {
      setLeaderboardStatus('No score was added for this game.');
    }
    document.getElementById('player-name').value = '';
    document.getElementById('player-name-error').innerText = '';
    document.getElementById('player-name').removeAttribute('aria-invalid');
  });
  document.getElementById('sudoku-board').addEventListener('input', validateBoard);
  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('use-hint').addEventListener('click', useHint);
  document.getElementById('check-solution').addEventListener('click', checkSolution);
  // initialize
  newGame();
});