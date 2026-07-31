import { dom } from './dom.js';

function applyTheme(theme) {
    if (theme === 'light') {
        document.documentElement.classList.remove('dark');
        dom.themeIcon.textContent = '☀️';
    } else {
        document.documentElement.classList.add('dark');
        dom.themeIcon.textContent = '🌙';
    }
}

export function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);

    dom.themeToggleBtn.addEventListener('click', () => {
        const isDark = document.documentElement.classList.contains('dark');
        const next = isDark ? 'light' : 'dark';
        applyTheme(next);
        localStorage.setItem('theme', next);
    });
}