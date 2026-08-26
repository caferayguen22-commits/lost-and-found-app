import { dom } from './dom-search.js';

let cachedLostItems = [];
let cachedFoundItems = [];

export function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function createItemCard(item) {
    const isFound = item.type === 'found';
    const badgeColor = isFound ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20';
    const shortId = item.tracking_code ? `#${item.tracking_code}` : `#${item._id.substring(item._id.length - 6).toUpperCase()}`;
    const matchBadge = item.match_found ? `<span class="px-2 py-0.5 text-xs rounded-md bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">🎉 Match</span>` : '';

    const card = document.createElement('div');
    card.className = 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 hover:border-gray-300 dark:hover:border-gray-700 transition-all flex flex-col justify-between';
    let imageMarkup = item.image ? `<img src="${item.image}" class="w-full h-32 object-cover rounded-xl mb-3 border border-gray-200 dark:border-gray-800">` : '';
    const claimButtonMarkup = isFound
        ? `<button type="button" class="claim-btn mt-3 w-full py-2 text-xs font-semibold rounded-lg bg-indigo-50 dark:bg-indigo-950/30 hover:bg-indigo-100 dark:hover:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-800/40 text-indigo-700 dark:text-indigo-300 transition-all" data-item-id="${item.id}">🕵️ Das könnte meins sein</button>`
        : '';

    card.innerHTML = `
        <div>
            ${imageMarkup}
            <div class="flex justify-between items-start mb-3">
                <div class="flex gap-2 items-center flex-wrap">
                    <span class="px-3 py-1 text-xs font-semibold rounded-full border ${badgeColor}">${isFound ? 'GEFUNDEN' : 'VERLOREN'}</span>
                    <span class="px-2 py-0.5 text-xs rounded-md bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700">${escapeHtml(item.category || 'Sonstiges')}</span>
                    ${matchBadge}
                </div>
                <span class="text-xs text-gray-500">Ort: ${escapeHtml(item.corrected_location || item.location || 'k.A.')}</span>
            </div>
            <h4 class="text-lg font-bold text-gray-900 dark:text-white mb-2">${escapeHtml(item.title)}</h4>
            <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-4">${escapeHtml(item.description)}</p>
            ${claimButtonMarkup}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-600 border-t border-gray-200 dark:border-gray-800 pt-3 flex justify-between items-center">
            <span class="font-mono text-indigo-600 dark:text-indigo-400 font-semibold">${shortId}</span>
            <span class="text-gray-500">In DB gespeichert</span>
        </div>
    `;
    return card;
}

function renderGrid(gridElement, items, emptyText) {
    if (!gridElement) return;
    gridElement.innerHTML = '';
    if (items.length === 0) {
        gridElement.innerHTML = `<div class="col-span-full text-center py-8 text-gray-500 bg-gray-100 dark:bg-gray-900/50 rounded-2xl border border-gray-200 dark:border-gray-800">${emptyText}</div>`;
        return;
    }
    items.slice().reverse().forEach(item => {
        gridElement.appendChild(createItemCard(item));
    });
}

function removeFilterBanner(gridElement) {
    const existing = gridElement.parentElement.querySelector('.filter-banner');
    if (existing) existing.remove();
}

function showFilterBanner(gridElement, category, onReset) {
    removeFilterBanner(gridElement);
    const banner = document.createElement('div');
    banner.className = 'filter-banner mb-3 flex items-center justify-between px-4 py-2 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/40 text-sm text-indigo-700 dark:text-indigo-200';
    banner.innerHTML = `<span>Gefiltert nach: <strong>${escapeHtml(category)}</strong></span>`;
    const resetBtn = document.createElement('button');
    resetBtn.type = 'button';
    resetBtn.className = 'text-xs font-semibold underline hover:no-underline';
    resetBtn.innerText = 'Alle anzeigen';
    resetBtn.addEventListener('click', onReset);
    banner.appendChild(resetBtn);
    gridElement.parentElement.insertBefore(banner, gridElement);
}

export async function loadDashboardItems() {
    if (!dom.lostItemsGrid && !dom.foundItemsGrid) return;
    try {
        const response = await fetch('/api/items');
        const items = await response.json();

        cachedLostItems = items.filter(item => item.type === 'lost');
        cachedFoundItems = items.filter(item => item.type === 'found');

        removeFilterBanner(dom.lostItemsGrid);
        removeFilterBanner(dom.foundItemsGrid);
        renderGrid(dom.lostItemsGrid, cachedLostItems, 'Noch keine Verlustmeldungen vorhanden.');
        renderGrid(dom.foundItemsGrid, cachedFoundItems, 'Noch keine Fundmeldungen vorhanden.');
    } catch (error) {
        console.error("Fehler beim Laden:", error);
    }
}

// type: 'lost' oder 'found' -- welche der beiden Listen gefiltert angezeigt wird
export function filterGridByCategory(type, category) {
    const gridElement = type === 'lost' ? dom.lostItemsGrid : dom.foundItemsGrid;
    const sourceItems = type === 'lost' ? cachedLostItems : cachedFoundItems;
    if (!gridElement) return;

    const filtered = sourceItems.filter(item => item.category === category);
    renderGrid(gridElement, filtered, `Keine ${category}-Meldungen in dieser Liste vorhanden.`);
    showFilterBanner(gridElement, category, () => {
        removeFilterBanner(gridElement);
        renderGrid(gridElement, sourceItems, type === 'lost' ? 'Noch keine Verlustmeldungen vorhanden.' : 'Noch keine Fundmeldungen vorhanden.');
    });

    gridElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
}