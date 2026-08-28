import { dom } from './dom.js';
import { initTheme } from './theme.js';
import { loadProductCatalog } from './catalog-api.js';
import { setMode, updateCategoryUI } from './chip-ui.js';
import { openForm, resetUI, handleFormSubmit, initImageInput, initPhotoAnalysisForItemForm, updateValuableItemHint, checkSecretFeatureOverlap } from './form.js';
import { renderAuthStatus } from './auth-status.js';

async function init() {
    await loadProductCatalog();

    initTheme();
    initImageInput();
    initPhotoAnalysisForItemForm();
    renderAuthStatus('auth-status');

    dom.btnLost.addEventListener('click', () => openForm('lost'));
    dom.btnFound.addEventListener('click', () => openForm('found'));
    dom.btnBack.addEventListener('click', resetUI);
    dom.btnReset.addEventListener('click', resetUI);
    dom.itemForm.addEventListener('submit', handleFormSubmit);

    dom.modeExpertBtn.addEventListener('click', () => setMode('expert'));
    dom.modeSimpleBtn.addEventListener('click', () => setMode('simple'));

    dom.categoryInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            updateCategoryUI(e.target.value);
            updateValuableItemHint();
        });
    });

    dom.itemEstimatedValueInput.addEventListener('input', updateValuableItemHint);

    dom.itemDescription.addEventListener('input', checkSecretFeatureOverlap);
    dom.itemSecretFeatureInput.addEventListener('input', checkSecretFeatureOverlap);
}

document.addEventListener('DOMContentLoaded', init);