import { dom } from './dom-search.js';
import { initTheme } from './theme.js';
import { loadDashboardItems, filterGridByCategory } from './dashboard.js';
import { initClaimFlow } from './claim.js';

async function init() {
    initTheme();
    initClaimFlow();

    if (dom.btnRefresh) dom.btnRefresh.addEventListener('click', loadDashboardItems);

    await loadDashboardItems();

    // Kommt man von der "🔍 Gemeldete X durchsuchen"-Verlinkung, gleich gefiltert anzeigen.
    const params = new URLSearchParams(window.location.search);
    const type = params.get('type');
    const category = params.get('category');
    if (type && category) {
        filterGridByCategory(type, category);
    }
}

document.addEventListener('DOMContentLoaded', init);
