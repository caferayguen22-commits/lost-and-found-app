import { initTheme } from './theme.js';

const RESULT_STYLES = {
    stolen: 'mt-4 p-4 rounded-xl text-sm bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/40 text-red-700 dark:text-red-300',
    lost: 'mt-4 p-4 rounded-xl text-sm bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/40 text-amber-700 dark:text-amber-300',
    safe_or_unknown: 'mt-4 p-4 rounded-xl text-sm bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/40 text-emerald-700 dark:text-emerald-300',
    error: 'mt-4 p-4 rounded-xl text-sm bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300'
};

function showResult(style, text) {
    const box = document.getElementById('check-result');
    box.className = style;
    box.innerText = text;
    box.classList.remove('hidden');
}

async function handleCheckSubmit(event) {
    event.preventDefault();
    const submitBtn = document.getElementById('check-submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerText = '⏳ Wird geprüft...';

    const marks = document.getElementById('check-marks').value.trim();

    try {
        const response = await fetch('/api/garage/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifying_marks: marks })
        });
        const data = await response.json();

        if (!response.ok) {
            showResult(RESULT_STYLES.error, data.message || 'Die Prüfung ist fehlgeschlagen.');
        } else if (!data.found) {
            showResult(RESULT_STYLES.safe_or_unknown, '✅ Kein Treffer -- dieser Gegenstand ist nicht als verloren/gestohlen registriert (das ist keine Garantie, nur ein Hinweis).');
        } else if (data.item.status === 'stolen') {
            showResult(RESULT_STYLES.stolen, `⚠️ Achtung: Als GESTOHLEN gemeldet (Kategorie: ${data.item.category}). Vom Kauf wird abgeraten.`);
        } else if (data.item.status === 'lost') {
            showResult(RESULT_STYLES.lost, `⚠️ Als VERLOREN gemeldet (Kategorie: ${data.item.category}).`);
        } else {
            showResult(RESULT_STYLES.safe_or_unknown, '✅ Registriert, aber nicht als verloren/gestohlen gemeldet.');
        }
    } catch (error) {
        showResult(RESULT_STYLES.error, 'Verbindungsfehler zum Server.');
        console.error(error);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Prüfen';
    }
}

function init() {
    initTheme();
    document.getElementById('check-form').addEventListener('submit', handleCheckSubmit);
}

document.addEventListener('DOMContentLoaded', init);
