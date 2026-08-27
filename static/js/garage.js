import { initTheme } from './theme.js';
import { renderAuthStatus } from './auth-status.js';

let base64Image = "";

const STATUS_LABELS = { safe: '✅ Sicher', lost: '❓ Verloren', stolen: '🚨 Gestohlen' };
const STATUS_BADGE_CLASS = {
    safe: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
    lost: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
    stolen: 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20'
};

function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function initImageInput() {
    const input = document.getElementById('garage-image');
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => { base64Image = reader.result; };
            reader.readAsDataURL(file);
        }
    });
}

function createGarageItemCard(item) {
    const card = document.createElement('div');
    card.className = 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5';

    const otherStatuses = Object.keys(STATUS_LABELS).filter(s => s !== item.status);
    const statusButtons = otherStatuses.map(s =>
        `<button type="button" class="status-btn text-xs font-semibold px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-800 hover:border-indigo-500 transition-all" data-item-id="${item.id}" data-status="${s}">${STATUS_LABELS[s]}</button>`
    ).join('');

    card.innerHTML = `
        <div class="flex justify-between items-start mb-3">
            <div class="flex gap-2 items-center flex-wrap">
                <span class="px-3 py-1 text-xs font-semibold rounded-full border ${STATUS_BADGE_CLASS[item.status]}">${STATUS_LABELS[item.status]}</span>
                <span class="px-2 py-0.5 text-xs rounded-md bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700">${escapeHtml(item.category)}</span>
            </div>
            <button type="button" class="delete-btn text-xs text-gray-400 hover:text-red-500 transition-colors" data-item-id="${item.id}">🗑 Löschen</button>
        </div>
        <h4 class="text-lg font-bold text-gray-900 dark:text-white mb-1">${escapeHtml(item.title)}</h4>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-3">${escapeHtml(item.description)}</p>
        ${item.identifying_marks ? `<p class="text-xs text-gray-400 dark:text-gray-600 mb-3">Merkmal: ${escapeHtml(item.identifying_marks)}</p>` : ''}
        <div class="flex gap-2 flex-wrap">${statusButtons}</div>
    `;
    return card;
}

async function loadGarageItems() {
    const listEl = document.getElementById('garage-items-list');
    try {
        const response = await fetch('/api/garage');
        const items = await response.json();

        listEl.innerHTML = '';
        if (!Array.isArray(items) || items.length === 0) {
            listEl.innerHTML = `<div class="text-center py-8 text-gray-500 bg-gray-100 dark:bg-gray-900/50 rounded-2xl border border-gray-200 dark:border-gray-800">Noch nichts registriert.</div>`;
            return;
        }
        items.forEach(item => listEl.appendChild(createGarageItemCard(item)));
    } catch (error) {
        console.error('Fehler beim Laden der Garage:', error);
    }
}

async function handleFormSubmit(event) {
    event.preventDefault();
    const submitBtn = document.getElementById('garage-submit-btn');
    submitBtn.disabled = true;

    const payload = {
        category: document.getElementById('garage-category').value.trim(),
        title: document.getElementById('garage-title').value.trim(),
        description: document.getElementById('garage-description').value.trim(),
        identifying_marks: document.getElementById('garage-marks').value.trim() || null,
        image: base64Image || null
    };

    try {
        const response = await fetch('/api/garage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (response.ok) {
            document.getElementById('garage-form').reset();
            base64Image = "";
            await loadGarageItems();
        } else {
            alert('Fehler: ' + (data.message || 'Registrieren fehlgeschlagen.'));
        }
    } catch (error) {
        alert('Verbindungsfehler zum Server.');
        console.error(error);
    } finally {
        submitBtn.disabled = false;
    }
}

async function handleListClick(event) {
    const statusBtn = event.target.closest('.status-btn');
    if (statusBtn) {
        const itemId = statusBtn.dataset.itemId;
        const newStatus = statusBtn.dataset.status;
        const response = await fetch(`/api/garage/${itemId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        if (response.ok) {
            await loadGarageItems();
        } else {
            const data = await response.json();
            alert('Fehler: ' + (data.message || 'Status konnte nicht geändert werden.'));
        }
        return;
    }

    const deleteBtn = event.target.closest('.delete-btn');
    if (deleteBtn) {
        if (!confirm('Diesen Gegenstand wirklich löschen?')) return;
        const itemId = deleteBtn.dataset.itemId;
        const response = await fetch(`/api/garage/${itemId}`, { method: 'DELETE' });
        if (response.ok) {
            await loadGarageItems();
        } else {
            const data = await response.json();
            alert('Fehler: ' + (data.message || 'Löschen fehlgeschlagen.'));
        }
    }
}

function init() {
    initTheme();
    renderAuthStatus('auth-status');
    initImageInput();

    document.getElementById('garage-form').addEventListener('submit', handleFormSubmit);
    document.getElementById('garage-items-list').addEventListener('click', handleListClick);

    loadGarageItems();
}

document.addEventListener('DOMContentLoaded', init);
