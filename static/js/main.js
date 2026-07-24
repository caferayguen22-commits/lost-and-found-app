document.addEventListener('DOMContentLoaded', () => {
    // DOM Elemente (wie zuvor)
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

    const brandContainer = document.getElementById('brand-selection-container');
    const brandButtonsDiv = document.getElementById('brand-buttons');
    const modelContainer = document.getElementById('model-selection-container');
    const modelChips = document.getElementById('model-chips');
    const imageInput = document.getElementById('item-image');

    let base64Image = "";

    // 2026 Datenbank: Marken basierend auf Kategorie
    const brandsByCategory = {
        'Smartphone': ['Apple', 'Samsung', 'Google', 'Xiaomi', 'OnePlus', 'Sony', 'Andere'],
        'Kopfhörer': ['Apple', 'Samsung', 'Sony', 'Bose', 'JBL', 'Sennheiser', 'Andere'],
        'Laptop/Tablet': ['Apple', 'Lenovo', 'HP', 'Dell', 'Microsoft', 'Samsung', 'Andere']
    };

    // 2026 Datenbank: Modelle basierend auf Marke und Kategorie
    const modelsDB = {
        'Smartphone': {
            'Apple': ['iPhone 17 Pro Max', 'iPhone 17 Pro', 'iPhone 17', 'iPhone 16 Pro', 'iPhone 15'],
            'Samsung': ['Galaxy S26 Ultra', 'Galaxy S26', 'Galaxy S25', 'Galaxy A56', 'Galaxy Z Flip 7'],
            'Google': ['Pixel 10 Pro', 'Pixel 10', 'Pixel 9 Pro', 'Pixel 8a'],
            'Xiaomi': ['Xiaomi 16 Pro', 'Xiaomi 15', 'Redmi Note 15', 'Poco X7'],
            'OnePlus': ['OnePlus 14', 'OnePlus 13', 'Nord 5'],
            'Sony': ['Xperia 1 VII', 'Xperia 5 VII']
        },
        'Kopfhörer': {
            'Apple': ['AirPods Pro (3. Gen)', 'AirPods (4. Gen)', 'AirPods Max 2', 'Beats Fit Pro'],
            'Samsung': ['Galaxy Buds 3 Pro', 'Galaxy Buds FE'],
            'Sony': ['WF-1000XM6 (In-Ear)', 'WH-1000XM6 (Over-Ear)', 'LinkBuds'],
            'Bose': ['QuietComfort Ultra', 'QC Earbuds'],
            'JBL': ['Tour Pro 3', 'Live Pro 2', 'Wave Beam'],
            'Sennheiser': ['Momentum True Wireless 4', 'Momentum 4 Over-Ear']
        },
        'Laptop/Tablet': {
            'Apple': ['MacBook Air M4', 'MacBook Pro M4', 'iPad Pro (M4)', 'iPad Air'],
            'Lenovo': ['ThinkPad X1 Carbon', 'IdeaPad', 'Yoga'],
            'HP': ['Spectre x360', 'Envy', 'Pavilion'],
            'Dell': ['XPS 13', 'XPS 15', 'Inspiron'],
            'Microsoft': ['Surface Pro 12', 'Surface Laptop 7'],
            'Samsung': ['Galaxy Book 5', 'Galaxy Tab S10']
        }
    };

    // Event Listener initialisieren
    btnLost.addEventListener('click', () => openForm('lost'));
    btnFound.addEventListener('click', () => openForm('found'));
    btnBack.addEventListener('click', resetUI);
    btnReset.addEventListener('click', resetUI);
    if (btnRefresh) btnRefresh.addEventListener('click', loadDashboardItems);
    itemForm.addEventListener('submit', handleFormSubmit);

    // Bild Konvertierung
    if (imageInput) {
        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onloadend = () => { base64Image = reader.result; };
                reader.readAsDataURL(file);
            }
        });
    }

    // Kategorie Wechsel logic
    categoryInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            updateCategoryUI(e.target.value);
        });
    });

    function updateCategoryUI(category) {
        // Formular-Zustand zurücksetzen
        modelContainer.classList.add('hidden');
        brandButtonsDiv.innerHTML = '';
        itemTitleInput.value = '';

        const supportedBrands = brandsByCategory[category];

        if (supportedBrands) {
            brandContainer.classList.remove('hidden');
            // Erzeuge dynamische Marken-Buttons
            supportedBrands.forEach(brand => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'brand-btn px-4 py-2 text-xs font-semibold rounded-xl bg-gray-950 border border-gray-800 hover:border-indigo-500 transition-all';
                btn.innerText = brand;
                btn.addEventListener('click', () => {
                    // Highlight aktiven Button
                    document.querySelectorAll('.brand-btn').forEach(b => b.classList.remove('border-indigo-500', 'bg-indigo-950/40'));
                    btn.classList.add('border-indigo-500', 'bg-indigo-950/40');
                    renderModels(category, brand);
                });
                brandButtonsDiv.appendChild(btn);
            });
        } else {
            // Kategorien wie Schlüssel oder Geldbörse haben keine Marken/Modelle
            brandContainer.classList.add('hidden');
        }

        // Tipps anpassen
        if (category === 'Kopfhörer') {
            safetyTipText.innerText = 'Tipp: Ladecase oder In-Ear einzeln verloren? Erwähne es in der Beschreibung!';
        } else if (category === 'Schlüssel') {
            safetyTipText.innerText = 'Tipp: Gib niemals deine genaue Wohnadresse als Fund/Verlustort bei Schlüsseln an!';
        } else {
            safetyTipText.innerText = 'Tipp für die Übergabe: Verabredet euch an einem belebten, öffentlichen Ort.';
        }
    }

    function renderModels(category, brand) {
        modelChips.innerHTML = '';
        const categoryModels = modelsDB[category];
        const models = categoryModels ? categoryModels[brand] || [] : [];

        if (models.length === 0) {
            modelContainer.classList.add('hidden');
            itemTitleInput.placeholder = `Modell von ${brand} hier eintragen...`;
            itemTitleInput.focus();
            return;
        }

        modelContainer.classList.remove('hidden');
        itemTitleInput.placeholder = 'Modell aus Liste wählen oder tippen...';
        models.forEach(mod => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-950 border border-gray-800 hover:border-indigo-400 text-gray-300 transition-all';
            chip.innerText = mod;
            chip.addEventListener('click', () => {
                itemTitleInput.value = mod;
            });
            modelChips.appendChild(chip);
        });
    }

    function openForm(type) {
        itemForm.reset();
        base64Image = "";
        itemTypeInput.value = type;
        formContainer.classList.remove('hidden');
        resultContainer.classList.add('hidden');

        // Initiales Setup für Standard-Kategorie (Smartphone)
        const defaultCategory = document.querySelector('input[name="category"]:checked')?.value || 'Smartphone';
        updateCategoryUI(defaultCategory);

        if (type === 'found') {
            formTitle.innerText = "Fundgegenstand erfassen";
            hintBox.innerText = "Danke für deine Ehrlichkeit! Präzise Details erhöhen die Chance extrem, den Eigentümer sofort zu finden.";
        } else {
            formTitle.innerText = "Verlustmeldung aufgeben";
            hintBox.innerText = "Beschreibe deinen Gegenstand so genau wie möglich. Unsere KI durchsucht sofort alle Meldungen.";
        }
        formContainer.scrollIntoView({ behavior: 'smooth' });
    }

    function resetUI() {
        formContainer.classList.add('hidden');
        resultContainer.classList.add('hidden');
        itemForm.reset();
        base64Image = "";
        loadDashboardItems();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Dashboard Load (Code bleibt identisch zum vorherigen)
    async function loadDashboardItems() {
        if (!itemsGrid) return;
        try {
            const response = await fetch('/api/items');
            const items = await response.json();
            itemsGrid.innerHTML = '';
            if (items.length === 0) {
                itemsGrid.innerHTML = `<div class="col-span-full text-center py-8 text-gray-500 bg-gray-900/50 rounded-2xl border border-gray-800">Noch keine Meldungen vorhanden.</div>`;
                return;
            }
            items.reverse().forEach(item => {
                const isFound = item.type === 'found';
                const badgeColor = isFound ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20';
                const shortId = `MATCH-#${item._id.substring(item._id.length - 6).toUpperCase()}`;
                const card = document.createElement('div');
                card.className = 'bg-gray-900 border border-gray-800 rounded-2xl p-5 hover:border-gray-700 transition-all flex flex-col justify-between';
                let imageMarkup = item.image ? `<img src="${item.image}" class="w-full h-32 object-cover rounded-xl mb-3 border border-gray-800">` : '';

                card.innerHTML = `
                    <div>
                        ${imageMarkup}
                        <div class="flex justify-between items-start mb-3">
                            <div class="flex gap-2 items-center">
                                <span class="px-3 py-1 text-xs font-semibold rounded-full border ${badgeColor}">${isFound ? 'GEFUNDEN' : 'VERLOREN'}</span>
                                <span class="px-2 py-0.5 text-xs rounded-md bg-gray-800 text-gray-400 border border-gray-700">${escapeHtml(item.category || 'Sonstiges')}</span>
                            </div>
                            <span class="text-xs text-gray-500">Ort: ${escapeHtml(item.location || 'k.A.')}</span>
                        </div>
                        <h4 class="text-lg font-bold text-white mb-2">${escapeHtml(item.title)}</h4>
                        <p class="text-sm text-gray-400 line-clamp-2 mb-4">${escapeHtml(item.description)}</p>
                    </div>
                    <div class="text-xs text-gray-600 border-t border-gray-800 pt-3 flex justify-between items-center">
                        <span class="font-mono text-indigo-400 font-semibold">${shortId}</span>
                        <span class="text-gray-500">In DB gespeichert</span>
                    </div>
                `;
                itemsGrid.appendChild(card);
            });
        } catch (error) {
            console.error("Fehler beim Laden:", error);
        }
    }

    // Form Submit (Code bleibt identisch)
    async function handleFormSubmit(event) {
        event.preventDefault();
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        submitBtn.innerText = "⏳ KI-Matching läuft...";

        const selectedCategory = document.querySelector('input[name="category"]:checked')?.value || 'Sonstiges';
        const payload = {
            type: itemTypeInput.value,
            category: selectedCategory,
            title: document.getElementById('item-title').value,
            description: document.getElementById('item-description').value,
            location: document.getElementById('item-location').value,
            image: base64Image
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
                resultContent.innerText = `✅ MELDUNG ERFOLGREICH ERFASST!\n--------------------------------------------------\n` + data.ai_report;
                resultContainer.scrollIntoView({ behavior: 'smooth' });
                loadDashboardItems();
            } else {
                alert("Fehler: " + (data.message || "Meldung konnte nicht angelegt werden."));
            }
        } catch (error) {
            alert("Verbindungsfehler zum Server.");
            console.error(error);
        } finally {
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            submitBtn.innerText = "Meldung absenden & KI-Matching starten";
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    loadDashboardItems();
});