namespace AutoworkRenderer {
  const themeStorageKey = "autowork-theme";

  export function getStoredTheme(): UiTheme {
    try {
      const storedTheme = window.localStorage.getItem(themeStorageKey);
      return storedTheme === "light" ? "light" : "dark";
    } catch {
      return "dark";
    }
  }

  export function applyTheme(theme: UiTheme): void {
    document.documentElement.dataset.theme = theme;
    try {
      window.localStorage.setItem(themeStorageKey, theme);
    } catch {
      // A restricted renderer can still use the theme for the current session.
    }
  }
}
