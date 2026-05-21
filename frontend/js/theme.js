const ThemeManager = {
  STORAGE_KEY: 'prepzo-theme',

  init() {
    const saved = localStorage.getItem(this.STORAGE_KEY);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    this.set(theme, false);
    this.bindToggles();
  },

  set(theme, animate = true) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(this.STORAGE_KEY, theme);
    document.querySelectorAll('[data-theme-label]').forEach(el => {
      el.textContent = theme === 'dark' ? 'Dark' : 'Light';
    });
    if (animate) {
      document.body.classList.add('page-enter');
      setTimeout(() => document.body.classList.remove('page-enter'), 400);
    }
  },

  toggle() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    this.set(current === 'dark' ? 'light' : 'dark');
  },

  bindToggles() {
    document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
      btn.addEventListener('click', () => this.toggle());
    });
  },
};

document.addEventListener('DOMContentLoaded', () => ThemeManager.init());
