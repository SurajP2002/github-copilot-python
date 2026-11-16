import assert from 'node:assert/strict';
import test from 'node:test';

import {
  addLeaderboardScore,
  LEADERBOARD_STORAGE_KEY,
  normalizePlayerName,
  readLeaderboard,
  sortLeaderboard,
  writeLeaderboard
} from '../static/leaderboard.mjs';

function createScore(timeSeconds, overrides = {}) {
  return {
    name: `Player ${timeSeconds}`,
    timeSeconds,
    difficulty: 'Easy',
    hintsUsed: 0,
    ...overrides
  };
}

function createStorage(initialValue = null) {
  const values = new Map();
  if (initialValue !== null) {
    values.set(LEADERBOARD_STORAGE_KEY, initialValue);
  }
  return {
    getItem(key) {
      return values.has(key) ? values.get(key) : null;
    },
    setItem(key, value) {
      values.set(key, value);
    }
  };
}

test('sorts scores by fastest time and preserves the first tied score', () => {
  const scores = [
    createScore(90, {name: 'Slower'}),
    createScore(35, {name: 'First tied'}),
    createScore(35, {name: 'Second tied'})
  ];

  assert.deepEqual(
    sortLeaderboard(scores).map(score => score.name),
    ['First tied', 'Second tied', 'Slower']
  );
});

test('keeps only the ten fastest scores when adding a score', () => {
  const existingScores = Array.from({length: 10}, (_, index) =>
    createScore(index + 20)
  );

  const updatedScores = addLeaderboardScore(existingScores, createScore(10));

  assert.equal(updatedScores.length, 10);
  assert.equal(updatedScores[0].timeSeconds, 10);
  assert.equal(updatedScores[9].timeSeconds, 28);
});

test('trims valid names and rejects missing, whitespace, and invalid names', () => {
  assert.equal(normalizePlayerName('  Sam  '), 'Sam');
  assert.equal(normalizePlayerName('   '), null);
  assert.equal(normalizePlayerName(undefined), null);
  assert.equal(normalizePlayerName('x'.repeat(41)), null);
  assert.equal(normalizePlayerName('Sam\nJones'), null);
});

test('loads missing data as an empty leaderboard and persists top ten scores', () => {
  const storage = createStorage();
  assert.deepEqual(readLeaderboard(storage), []);

  const scores = Array.from({length: 12}, (_, index) =>
    createScore(60 - index)
  );
  const savedScores = writeLeaderboard(storage, scores);

  assert.equal(savedScores.length, 10);
  assert.deepEqual(readLeaderboard(storage), savedScores);
});

test('rejects malformed or invalid saved data without overwriting it', () => {
  const invalidJson = '{invalid';
  const storage = createStorage(invalidJson);

  assert.throws(() => readLeaderboard(storage), /valid JSON/);
  assert.equal(storage.getItem(LEADERBOARD_STORAGE_KEY), invalidJson);

  const invalidScores = createStorage(JSON.stringify([createScore(10, {name: ' '})]));
  assert.throws(() => readLeaderboard(invalidScores), /invalid score/);
});

test('rejects score records with invalid fields', () => {
  assert.throws(
    () => sortLeaderboard([createScore(-1)]),
    /invalid score/
  );
  assert.throws(
    () => sortLeaderboard([createScore(20, {difficulty: 'Expert'})]),
    /invalid score/
  );
  assert.throws(
    () => sortLeaderboard([createScore(20, {hintsUsed: -1})]),
    /invalid score/
  );
});
