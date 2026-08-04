import { dom } from './dom.js';

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
    items.reverse().forEach(item => {
        gridElement.appendChild(createItemCard(item));
    });
}

export async function loadDashboardItems() {
    if (!dom.lostItemsGrid && !dom.foundItemsGrid) return;
    try {
        const response = await fetch('/api/items');
        const items = await response.json();

        const lostItems = items.filter(item => item.type === 'lost');
        const foundItems = items.filter(item => item.type === 'found');

        renderGrid(dom.lostItemsGrid, lostItems, 'Noch keine Verlustmeldungen vorhanden.');
        renderGrid(dom.foundItemsGrid, foundItems, 'Noch keine Fundmeldungen vorhanden.');
    } catch (error) {
        console.error("Fehler beim Laden:", error);
    }
}