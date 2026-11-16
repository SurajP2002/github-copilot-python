export const THEME_STORAGE_KEY = 'sudokuTheme';

export function readTheme(storage) {
  const savedTheme = storage.getItem(THEME_STORAGE_KEY);
  return savedTheme === 'dark' ? 'dark' : 'light';
}

export function writeTheme(storage, theme) {
  if (theme !== 'light' && theme !== 'dark') {
    throw new TypeError('Theme must be light or dark.');
  }

  storage.setItem(THEME_STORAGE_KEY, theme);
}
