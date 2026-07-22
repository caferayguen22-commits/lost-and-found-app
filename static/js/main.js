document.addEventListener('DOMContentLoaded', () => {
    // DOM Elemente selektieren
    const btnLost = document.getElementById('btn-lost');
    const btnFound = document.getElementById('btn-found');
    const btnBack = document.getElementById('btn-back');
    const btnReset = document.getElementById('btn-reset');
    const btnRefresh = document.getElementById('btn-refresh');

    const formContainer = document.getElementById('form-container');
    const resultContainer = document.getElementById('result-container');
    const itemsGrid = document.getElementById('items-grid');
    const itemForm = document.getElementById('item-form');
    const submitBtn = document.getElementById('submit-btn');

    const itemTypeInput = document.getElementById('item-type');
    const itemTitleInput = document.getElementById('item-title');
    const formTitle = document.getElementById('form-title');
    const hintBox = document.getElementById('hint-box');
    const resultContent = document.getElementById('result-content');

    const categoryInputs = document.querySelectorAll('input[name="category"]');
    const safetyTipText = document.getElementById('safety-tip-text');

    // Mappings für dynamische Placeholders & Sicherheitstipps
    const categoryConfig = {
        'Smartphone': {
            placeholder: 'z. B. iPhone 15 Pro Max, Samsung Galaxy S24',
            safetyTip: 'Tipp für die Übergabe: Verabredet euch an einem gut erreichbaren, öffentlichen Ort in eurer Nähe – genau wie bei Kleinanzeigen.'
        },
        'Schlüssel': {
            placeholder: 'z. B. Haustürschlüssel mit rotem Anhänger',
            safetyTip: 'Sicherheitstipp: Da Schlüssel direkt zur Haustür führen, verabredet euch am besten an einem belebten öffentlichen Ort oder nutzt eine Polizeidienststelle zur Übergabe.'
        },
        'Geldbörse': {
            placeholder: 'z. B. Schwarzes Leder-Portemonnaie, Ausweis enthalten',
            safetyTip: 'Tipp für die Übergabe: Verabredet euch an einem gut erreichbaren, öffentlichen Ort in eurer Nähe.'
        },
        'Sonstiges': {
            placeholder: 'z. B. Blaues Rucksack, Brille, Regenschirm',
            safetyTip: 'Tipp für die Übergabe: Verabredet euch an einem gut erreichbaren, öffentlichen Ort in eurer Nähe.'
        }
    };

    // Event Listener für Buttons
    btnLost.addEventListener('click', () => openForm('lost'));
    btnFound.addEventListener('click', () => openForm('found'));
    btnBack.addEventListener('click', resetUI);
    btnReset.addEventListener('click', resetUI);
    if (btnRefresh) btnRefresh.addEventListener('click', loadDashboardItems);
    itemForm.addEventListener('submit', handleFormSubmit);

    // Event Listener für Kategorien
    categoryInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            updateCategoryUI(e.target.value);
        });
    });

    // Beim ersten Laden direkt Dashboard befüllen
    loadDashboardItems();

    function updateCategoryUI(category) {
        const config = categoryConfig[category] || categoryConfig['Sonstiges'];
        if (itemTitleInput) itemTitleInput.placeholder = config.placeholder;
        if (safetyTipText) safetyTipText.innerText = config.safetyTip;
    }

    function openForm(type) {
        // Formular vor jedem Öffnen leeren
        itemForm.reset();

        itemTypeInput.value = type;
        formContainer.classList.remove('hidden');
        resultContainer.classList.add('hidden');

        // Standard-Kategorie UI anpassen
        const defaultCategory = document.querySelector('input[name="category"]:checked')?.value || 'Smartphone';
        updateCategoryUI(defaultCategory);

        if (type === 'found') {
            formTitle.innerText = "Fundgegenstand erfassen";
            hintBox.innerText = "Danke für deine Ehrlichkeit! Präzise Details zu Farbe, Schäden oder Sperrbildschirmen erhöhen die Chance extrem, den Eigentümer sofort zu finden.";
        } else {
            formTitle.innerText = "Verlustmeldung aufgeben";
            hintBox.innerText = "Beschreibe deinen Gegenstand so genau wie möglich. Unsere KI durchsucht sofort alle vorliegenden Fundmeldungen nach einer Übereinstimmung.";
        }

        formContainer.scrollIntoView({ behavior: 'smooth' });
    }

    function resetUI() {
        formContainer.classList.add('hidden');
        resultContainer.classList.add('hidden');
        itemForm.reset();
        loadDashboardItems();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async function loadDashboardItems() {
        if (!itemsGrid) return;

        try {
            const response = await fetch('/api/items');
            const items = await response.json();

            itemsGrid.innerHTML = '';

            if (items.length === 0) {
                itemsGrid.innerHTML = `
                    <div class="col-span-full text-center py-8 text-gray-500 bg-gray-900/50 rounded-2xl border border-gray-800">
                        Noch keine Meldungen vorhanden. Sei der Erste!
                    </div>`;
                return;
            }

            // Neueste Meldungen zuerst anzeigen
            items.reverse().forEach(item => {
                const isFound = item.type === 'found';
                const badgeColor = isFound
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-red-500/10 text-red-400 border-red-500/20';

                const card = document.createElement('div');
                card.className = 'bg-gray-900 border border-gray-800 rounded-2xl p-5 hover:border-gray-700 transition-all flex flex-col justify-between';
                card.innerHTML = `
                    <div>
                        <div class="flex justify-between items-start mb-3">
                            <div class="flex gap-2 items-center">
                                <span class="px-3 py-1 text-xs font-semibold rounded-full border ${badgeColor}">
                                    ${isFound ? 'GEFUNDEN' : 'VERLOREN'}
                                </span>
                                <span class="px-2 py-0.5 text-xs rounded-md bg-gray-800 text-gray-400 border border-gray-700">
                                    ${escapeHtml(item.category || 'Sonstiges')}
                                </span>
                            </div>
                            <span class="text-xs text-gray-500">Ort: ${escapeHtml(item.location || 'k.A.')}</span>
                        </div>
                        <h4 class="text-lg font-bold text-white mb-2">${escapeHtml(item.title)}</h4>
                        <p class="text-sm text-gray-400 line-clamp-2 mb-4">${escapeHtml(item.description)}</p>
                    </div>
                    <div class="text-xs text-gray-600 border-t border-gray-800 pt-3 flex justify-between items-center">
                        <span>ID: ${item._id.substring(0, 8)}...</span>
                        <span class="text-indigo-400 font-medium">In DB gespeichert</span>
                    </div>
                `;
                itemsGrid.appendChild(card);
            });

        } catch (error) {
            console.error("Fehler beim Laden der Dashboard-Items:", error);
        }
    }

    async function handleFormSubmit(event) {
        event.preventDefault();

        // SCHUTZ VOR DOPPELT-KLICKEN: Button sofort sperren & Text anpassen
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        submitBtn.innerText = "⏳ KI-Matching läuft... Bitte nicht schließen...";

        const selectedCategory = document.querySelector('input[name="category"]:checked')?.value || 'Sonstiges';

        const payload = {
            type: itemTypeInput.value,
            category: selectedCategory,
            title: document.getElementById('item-title').value,
            description: document.getElementById('item-description').value,
            location: document.getElementById('item-location').value
        };

        try {
            const response = await fetch('/api/items', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                formContainer.classList.add('hidden');
                resultContainer.classList.remove('hidden');

                // Bestätigungshinweis + KI-Bericht zusammensetzen
                const confirmationBanner = `✅ MELDUNG ERFOLGREICH ERFASST!\n` +
                    `--------------------------------------------------\n` +
                    `💡 Hinweis: Hast du alle wichtigen Details (Kratzer, Hülle, Farbe) angegeben? Je genauer die Angaben, desto präziser matchen unsere Algorithmen.\n\n`;

                resultContent.innerText = confirmationBanner + data.ai_report;
                resultContainer.scrollIntoView({ behavior: 'smooth' });
                loadDashboardItems();
            } else {
                alert("Fehler: " + (data.message || "Meldung konnte nicht angelegt werden."));
            }
        } catch (error) {
            alert("Verbindungsfehler zum Server.");
            console.error(error);
        } finally {
            // Button wieder freigeben
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            submitBtn.innerText = "Meldung absenden & KI-Matching starten";
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});