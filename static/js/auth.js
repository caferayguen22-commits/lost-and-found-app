import { initTheme } from './theme.js';

function showError(el, message) {
    el.textContent = message;
    el.classList.remove('hidden');
}

function safeNextPath() {
    const next = new URLSearchParams(window.location.search).get('next');
    if (next && next.startsWith('/') && !next.startsWith('//')) {
        return next;
    }
    return '/';
}

async function submitAuthForm(url, payload, errorBoxId, submitBtnId) {
    const errorBox = document.getElementById(errorBoxId);
    const submitBtn = document.getElementById(submitBtnId);
    errorBox.classList.add('hidden');
    submitBtn.disabled = true;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (response.ok) {
            window.location.href = safeNextPath();
        } else {
            showError(errorBox, data.message || 'Das hat leider nicht geklappt.');
        }
    } catch (error) {
        showError(errorBox, 'Verbindungsfehler zum Server.');
        console.error(error);
    } finally {
        submitBtn.disabled = false;
    }
}

function initRegisterForm() {
    const form = document.getElementById('register-form');
    if (!form) return;
    form.addEventListener('submit', (event) => {
        event.preventDefault();
        submitAuthForm('/api/register', {
            email: document.getElementById('register-email').value.trim(),
            password: document.getElementById('register-password').value
        }, 'register-error', 'register-submit-btn');
    });
}

function initLoginForm() {
    const form = document.getElementById('login-form');
    if (!form) return;
    form.addEventListener('submit', (event) => {
        event.preventDefault();
        submitAuthForm('/api/login', {
            email: document.getElementById('login-email').value.trim(),
            password: document.getElementById('login-password').value
        }, 'login-error', 'login-submit-btn');
    });
}

function init() {
    initTheme();
    initRegisterForm();
    initLoginForm();
}

document.addEventListener('DOMContentLoaded', init);
