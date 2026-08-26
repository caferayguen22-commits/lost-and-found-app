import { dom } from './dom-search.js';

let currentItemId = null;

const RESULT_STYLES = {
    match: 'mt-4 p-4 rounded-xl text-sm bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/40 text-emerald-700 dark:text-emerald-300',
    noMatch: 'mt-4 p-4 rounded-xl text-sm bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300',
    error: 'mt-4 p-4 rounded-xl text-sm bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/40 text-red-700 dark:text-red-300'
};

function showResult(style, text) {
    dom.claimResult.className = style;
    dom.claimResult.innerText = text;
    dom.claimResult.classList.remove('hidden');
}

function openClaimModal(itemId) {
    currentItemId = itemId;
    dom.claimForm.reset();
    dom.claimResult.classList.add('hidden');
    dom.claimModal.classList.remove('hidden');
}

function closeClaimModal() {
    dom.claimModal.classList.add('hidden');
    currentItemId = null;
}

async function submitClaim(event) {
    event.preventDefault();
    if (!currentItemId) return;

    dom.claimSubmitBtn.disabled = true;
    dom.claimSubmitBtn.innerText = "⏳ Wird geprüft...";

    const payload = {
        secret_feature_guess: dom.claimSecretGuessInput.value.trim(),
        claimant_email: dom.claimEmailInput.value.trim()
    };

    try {
        const response = await fetch(`/api/items/${currentItemId}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (response.status === 429 || !response.ok) {
            showResult(RESULT_STYLES.error, data.message || 'Die Prüfung ist fehlgeschlagen.');
        } else if (data.match) {
            showResult(RESULT_STYLES.match, '✅ Stimmt! Der Finder wurde benachrichtigt und meldet sich vielleicht bei dir.');
        } else {
            showResult(RESULT_STYLES.noMatch, data.message || '❌ Das stimmt leider nicht mit dem hinterlegten Merkmal überein.');
        }
    } catch (error) {
        showResult(RESULT_STYLES.error, 'Verbindungsfehler zum Server.');
        console.error(error);
    } finally {
        dom.claimSubmitBtn.disabled = false;
        dom.claimSubmitBtn.innerText = "Prüfen";
    }
}

export function initClaimFlow() {
    if (!dom.claimModal) return;

    document.addEventListener('click', (e) => {
        const claimBtn = e.target.closest('.claim-btn');
        if (claimBtn) {
            openClaimModal(claimBtn.dataset.itemId);
        }
    });

    dom.claimModalClose.addEventListener('click', closeClaimModal);
    dom.claimModal.addEventListener('click', (e) => {
        if (e.target === dom.claimModal) closeClaimModal();
    });
    dom.claimForm.addEventListener('submit', submitClaim);
}
