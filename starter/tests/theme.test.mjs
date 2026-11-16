import assert from 'node:assert/strict';
import test from 'node:test';

import {
  readTheme,
  THEME_STORAGE_KEY,
  writeTheme
} from '../static/theme.mjs';

function createStorage(initialTheme = null) {
  const values = new Map();
  if (initialTheme !== null) {
    values.set(THEME_STORAGE_KEY, initialTheme);
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

test('uses light mode when no recognized theme is saved', () => {
  assert.equal(readTheme(createStorage()), 'light');
  assert.equal(readTheme(createStorage('system')), 'light');
});

test('loads and saves the selected theme', () => {
  const storage = createStorage();

  writeTheme(storage, 'dark');
  assert.equal(storage.getItem(THEME_STORAGE_KEY), 'dark');
  assert.equal(readTheme(storage), 'dark');
});

test('rejects unsupported themes without changing saved data', () => {
  const storage = createStorage('dark');

  assert.throws(() => writeTheme(storage, 'blue'), /light or dark/);
  assert.equal(storage.getItem(THEME_STORAGE_KEY), 'dark');
});
