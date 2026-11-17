export const LEADERBOARD_STORAGE_KEY = 'sudokuLeaderboard';
export const MAX_LEADERBOARD_ENTRIES = 10;

const VALID_DIFFICULTIES = new Set(['Easy', 'Medium', 'Hard']);
const MAX_PLAYER_NAME_LENGTH = 40;

export function normalizePlayerName(name) {
  if (typeof name !== 'string') return null;

  const normalizedName = name.trim();
  if (
    normalizedName.length === 0 ||
    normalizedName.length > MAX_PLAYER_NAME_LENGTH ||
    /[\u0000-\u001f\u007f]/.test(normalizedName)
  ) {
    return null;
  }

  return normalizedName;
}

function validateScore(score) {
  if (score === null || typeof score !== 'object' || Array.isArray(score)) {
    throw new TypeError('Leaderboard contains an invalid score.');
  }

  const name = normalizePlayerName(score.name);
  if (
    name === null ||
    name !== score.name ||
    !Number.isSafeInteger(score.timeSeconds) ||
    score.timeSeconds < 0 ||
    !VALID_DIFFICULTIES.has(score.difficulty) ||
    !Number.isSafeInteger(score.hintsUsed) ||
    score.hintsUsed < 0
  ) {
    throw new TypeError('Leaderboard contains an invalid score.');
  }

  return {
    name,
    timeSeconds: score.timeSeconds,
    difficulty: score.difficulty,
    hintsUsed: score.hintsUsed
  };
}

export function sortLeaderboard(scores) {
  if (!Array.isArray(scores)) {
    throw new TypeError('Leaderboard data must be an array.');
  }

  return scores
    .map(validateScore)
    .sort((first, second) =>
      first.timeSeconds - second.timeSeconds ||
      first.hintsUsed - second.hintsUsed
    )
    .slice(0, MAX_LEADERBOARD_ENTRIES);
}

export function addLeaderboardScore(scores, score) {
  return sortLeaderboard([...scores, score]);
}

export function readLeaderboard(storage) {
  const savedData = storage.getItem(LEADERBOARD_STORAGE_KEY);
  if (savedData === null) return [];

  let scores;
  try {
    scores = JSON.parse(savedData);
  } catch {
    throw new TypeError('Saved leaderboard data is not valid JSON.');
  }

  return sortLeaderboard(scores);
}

export function writeLeaderboard(storage, scores) {
  const topScores = sortLeaderboard(scores);
  storage.setItem(LEADERBOARD_STORAGE_KEY, JSON.stringify(topScores));
  return topScores;
}
