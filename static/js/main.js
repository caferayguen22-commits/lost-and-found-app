import { dom } from './dom.js';
import { initTheme } from './theme.js';
import { loadProductCatalog } from './catalog-api.js';
import { setMode, updateCategoryUI } from './chip-ui.js';
import { loadDashboardItems } from './dashboard.js';
import { openForm, resetUI, handleFormSubmit, initImageInput } from './form.js';

async function init() {
    await loadProductCatalog();

    initTheme();
    initImageInput();

    dom.btnLost.addEventListener('click', () => openForm('lost'));
    dom.btnFound.addEventListener('click', () => openForm('found'));
    dom.btnBack.addEventListener('click', resetUI);
    dom.btnReset.addEventListener('click', resetUI);
    if (dom.btnRefresh) dom.btnRefresh.addEventListener('click', loadDashboardItems);
    dom.itemForm.addEventListener('submit', handleFormSubmit);

    dom.modeExpertBtn.addEventListener('click', () => setMode('expert'));
    dom.modeSimpleBtn.addEventListener('click', () => setMode('simple'));

    dom.categoryInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            updateCategoryUI(e.target.value);
        });
    });

    loadDashboardItems();
}

document.addEventListener('DOMContentLoaded', init);