document.addEventListener('DOMContentLoaded', async () => {
    // DOM Elemente
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
    const titleFieldContainer = document.getElementById('title-field-container');
    const formTitle = document.getElementById('form-title');
    const hintBox = document.getElementById('hint-box');
    const resultContent = document.getElementById('result-content');
    const itemDescription = document.getElementById('item-description');

    const categoryInputs = document.querySelectorAll('input[name="category"]');
    const safetyTipText = document.getElementById('safety-tip-text');

    const brandContainer = document.getElementById('brand-selection-container');
    const brandButtonsDiv = document.getElementById('brand-buttons');
    const seriesContainer = document.getElementById('series-selection-container');
    const seriesChipsDiv = document.getElementById('series-chips');
    const variantContainer = document.getElementById('variant-selection-container');
    const variantChipsDiv = document.getElementById('variant-chips');

    const expertModeContainer = document.getElementById('expert-mode-container');
    const simpleModeContainer = document.getElementById('simple-mode-container');
    const modeToggleContainer = document.getElementById('mode-toggle-container');
    const modeExpertBtn = document.getElementById('mode-expert-btn');
    const modeSimpleBtn = document.getElementById('mode-simple-btn');

    const colorChipsDiv = document.getElementById('color-chips');
    const caseSelectionContainer = document.getElementById('case-selection-container');
    const caseChipsDiv = document.getElementById('case-chips');
    const caseLabel = document.getElementById('case-label');

    const imageInput = document.getElementById('item-image');
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');

    let base64Image = "";
    let currentMode = 'expert'; // 'expert' | 'simple'
    let selectedColor = null;
    let selectedCase = null;

    // ---------------------------------------------------------------
    // THEME (Dark / Light) — Präferenz wird im echten Browser des
    // Nutzers per localStorage gespeichert (kein Claude-Artifact-Kontext,
    // hier ist localStorage völlig normal und persistent).
    // ---------------------------------------------------------------
    function applyTheme(theme) {
        if (theme === 'light') {
            document.documentElement.classList.remove('dark');
            themeIcon.textContent = '☀️';
        } else {
            document.documentElement.classList.add('dark');
            themeIcon.textContent = '🌙';
        }
    }

    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);

    themeToggleBtn.addEventListener('click', () => {
        const isDark = document.documentElement.classList.contains('dark');
        const next = isDark ? 'light' : 'dark';
        applyTheme(next);
        localStorage.setItem('theme', next);
    });

    // ---------------------------------------------------------------
    // PRODUKT-KATALOG — wird jetzt vom Server geladen (Python-Backend),
    // nicht mehr hier hartcodiert.
    // ---------------------------------------------------------------
    let productDB = {};
    let colorOptions = [];
    let caseOptionsByCategory = {};

    async function loadProductCatalog() {
        try {
            const response = await fetch('/api/product-catalog');
            const data = await response.json();
            productDB = data.brands;
            colorOptions = data.colors;
            caseOptionsByCategory = data.cases;
        } catch (error) {
            console.error("Produktkatalog konnte nicht geladen werden:", error);
        }
    }

    loadProductCatalog();

    // ---------------------------------------------------------------
    // EVENT LISTENER
    // ---------------------------------------------------------------
    btnLost.addEventListener('click', () => openForm('lost'));
    btnFound.addEventListener('click', () => openForm('found'));
    btnBack.addEventListener('click', resetUI);
    btnReset.addEventListener('click', resetUI);
    if (btnRefresh) btnRefresh.addEventListener('click', loadDashboardItems);
    itemForm.addEventListener('submit', handleFormSubmit);

    modeExpertBtn.addEventListener('click', () => setMode('expert'));
    modeSimpleBtn.addEventListener('click', () => setMode('simple'));

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

    categoryInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            updateCategoryUI(e.target.value);
        });
    });

    // ---------------------------------------------------------------
    // MODUS-UMSCHALTER (Kenner <-> Laie)
    // ---------------------------------------------------------------
    function setMode(mode) {
        currentMode = mode;
        const activeClasses = ['border-indigo-500', 'bg-indigo-100', 'dark:bg-indigo-950/30', 'text-gray-900', 'dark:text-white'];
        const inactiveClasses = ['border-gray-200', 'dark:border-gray-800', 'bg-gray-100', 'dark:bg-gray-950', 'text-gray-600', 'dark:text-gray-300'];

        [modeExpertBtn, modeSimpleBtn].forEach(btn => {
            btn.classList.remove(...activeClasses, ...inactiveClasses);
        });

        if (mode === 'expert') {
            modeExpertBtn.classList.add(...activeClasses);
            modeSimpleBtn.classList.add(...inactiveClasses);
            expertModeContainer.classList.remove('hidden');
            simpleModeContainer.classList.add('hidden');
        } else {
            modeSimpleBtn.classList.add(...activeClasses);
            modeExpertBtn.classList.add(...inactiveClasses);
            expertModeContainer.classList.add('hidden');
            simpleModeContainer.classList.remove('hidden');
            const category = document.querySelector('input[name="category"]:checked')?.value || 'Sonstiges';
            renderSimpleMode(category);
        }
    }

    // ---------------------------------------------------------------
    // KATEGORIE-WECHSEL
    // ---------------------------------------------------------------
    function updateCategoryUI(category) {
        brandButtonsDiv.innerHTML = '';
        seriesChipsDiv.innerHTML = '';
        variantChipsDiv.innerHTML = '';
        seriesContainer.classList.add('hidden');
        variantContainer.classList.add('hidden');
        itemTitleInput.value = '';

        const brandsForCategory = productDB[category];

        // Nur Kategorien mit einer Marken-Datenbank bekommen den
        // Kenner/Laie-Umschalter — bei Schlüssel/Geldbörse etc. gibt's
        // ohnehin keine Modell-Tiefe, da reicht direkt die Beschreibung.
        if (brandsForCategory) {
            modeToggleContainer.classList.remove('hidden');
            brandContainer.classList.remove('hidden');
            Object.keys(brandsForCategory).forEach(brand => {
                const btn = createChip(brand, () => {
                    setActiveChip(brandButtonsDiv, btn);
                    renderSeries(category, brand);
                });
                brandButtonsDiv.appendChild(btn);
            });
        } else {
            modeToggleContainer.classList.add('hidden');
            brandContainer.classList.add('hidden');
            setMode('expert'); // Titel-Feld bleibt die einzige Eingabe
        }

        if (caseOptionsByCategory[category]) {
            caseSelectionContainer.classList.remove('hidden');
            caseLabel.textContent = caseOptionsByCategory[category].label;
        } else {
            caseSelectionContainer.classList.add('hidden');
        }

        if (currentMode === 'simple') {
            renderSimpleMode(category);
        }

        if (category === 'Kopfhörer') {
            safetyTipText.innerText = 'Tipp: Ladecase oder In-Ear einzeln verloren? Erwähne es in der Beschreibung!';
        } else if (category === 'Schlüssel') {
            safetyTipText.innerText = 'Tipp: Gib niemals deine genaue Wohnadresse als Fund/Verlustort bei Schlüsseln an!';
        } else {
            safetyTipText.innerText = 'Tipp für die Übergabe: Verabredet euch an einem belebten, öffentlichen Ort.';
        }
    }

    function renderSeries(category, brand) {
        seriesChipsDiv.innerHTML = '';
        variantChipsDiv.innerHTML = '';
        variantContainer.classList.add('hidden');
        itemTitleInput.value = '';

        const seriesMap = productDB[category]?.[brand] || {};
        const seriesNames = Object.keys(seriesMap);

        if (seriesNames.length === 0) {
            seriesContainer.classList.add('hidden');
            itemTitleInput.placeholder = `Modell von ${brand} hier eintragen...`;
            itemTitleInput.focus();
            return;
        }

        seriesContainer.classList.remove('hidden');
        seriesNames.forEach(serie => {
            const btn = createChip(serie, () => {
                setActiveChip(seriesChipsDiv, btn);
                renderVariants(seriesMap[serie]);
            });
            seriesChipsDiv.appendChild(btn);
        });
    }

    function renderVariants(variants) {
        variantChipsDiv.innerHTML = '';

        // Nur EINE Variante -> keine zusätzliche Auswahl nötig, direkt übernehmen
        if (variants.length <= 1) {
            variantContainer.classList.add('hidden');
            itemTitleInput.value = variants[0] || '';
            return;
        }

        variantContainer.classList.remove('hidden');
        itemTitleInput.value = '';
        itemTitleInput.placeholder = 'Variante oben wählen oder hier tippen...';
        variants.forEach(variant => {
            const btn = createChip(variant, () => {
                setActiveChip(variantChipsDiv, btn);
                itemTitleInput.value = variant;
            });
            variantChipsDiv.appendChild(btn);
        });
    }

    // ---------------------------------------------------------------
    // LAIEN-MODUS: nur Farbe + Hülle, kein Modellwissen nötig
    // ---------------------------------------------------------------
    function renderSimpleMode(category) {
        colorChipsDiv.innerHTML = '';
        caseChipsDiv.innerHTML = '';
        selectedColor = null;
        selectedCase = null;

        colorOptions.forEach(color => {
            const btn = createChip(color, () => {
                setActiveChip(colorChipsDiv, btn);
                selectedColor = color;
            });
            colorChipsDiv.appendChild(btn);
        });

        const caseConfig = caseOptionsByCategory[category];
        if (caseConfig) {
            caseConfig.options.forEach(opt => {
                const btn = createChip(opt, () => {
                    setActiveChip(caseChipsDiv, btn);
                    selectedCase = opt;
                });
                caseChipsDiv.appendChild(btn);
            });
        }
    }

    // ---------------------------------------------------------------
    // HELFER: einheitlicher Chip-Button (hell + dunkel)
    // ---------------------------------------------------------------
    function createChip(label, onClick) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'chip-btn px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 hover:border-indigo-400 text-gray-700 dark:text-gray-300 transition-all';
        btn.innerText = label;
        btn.addEventListener('click', onClick);
        return btn;
    }

    function setActiveChip(container, activeBtn) {
        container.querySelectorAll('.chip-btn').forEach(b => {
            b.classList.remove('border-indigo-500', 'bg-indigo-100', 'dark:bg-indigo-950/40', 'text-gray-900', 'dark:text-white');
        });
        activeBtn.classList.add('border-indigo-500', 'bg-indigo-100', 'dark:bg-indigo-950/40', 'text-gray-900', 'dark:text-white');
    }

    // ---------------------------------------------------------------
    // FORMULAR ÖFFNEN / ZURÜCKSETZEN
    // ---------------------------------------------------------------
    function openForm(type) {
        itemForm.reset();
        base64Image = "";
        itemTypeInput.value = type;
        formContainer.classList.remove('hidden');
        resultContainer.classList.add('hidden');

        const defaultCategory = document.querySelector('input[name="category"]:checked')?.value || 'Smartphone';
        setMode('expert');
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

    // ---------------------------------------------------------------
    // DASHBOARD LADEN
    // ---------------------------------------------------------------
    async function loadDashboardItems() {
        if (!itemsGrid) return;
        try {
            const response = await fetch('/api/items');
            const items = await response.json();
            itemsGrid.innerHTML = '';
            if (items.length === 0) {
                itemsGrid.innerHTML = `<div class="col-span-full text-center py-8 text-gray-500 bg-gray-100 dark:bg-gray-900/50 rounded-2xl border border-gray-200 dark:border-gray-800">Noch keine Meldungen vorhanden.</div>`;
                return;
            }
            items.reverse().forEach(item => {
                const isFound = item.type === 'found';
                const badgeColor = isFound ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20';
                const shortId = `MATCH-#${item._id.substring(item._id.length - 6).toUpperCase()}`;
                const card = document.createElement('div');
                card.className = 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 hover:border-gray-300 dark:hover:border-gray-700 transition-all flex flex-col justify-between';
                let imageMarkup = item.image ? `<img src="${item.image}" class="w-full h-32 object-cover rounded-xl mb-3 border border-gray-200 dark:border-gray-800">` : '';

                card.innerHTML = `
                    <div>
                        ${imageMarkup}
                        <div class="flex justify-between items-start mb-3">
                            <div class="flex gap-2 items-center">
                                <span class="px-3 py-1 text-xs font-semibold rounded-full border ${badgeColor}">${isFound ? 'GEFUNDEN' : 'VERLOREN'}</span>
                                <span class="px-2 py-0.5 text-xs rounded-md bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700">${escapeHtml(item.category || 'Sonstiges')}</span>
                            </div>
                            <span class="text-xs text-gray-500">Ort: ${escapeHtml(item.location || 'k.A.')}</span>
                        </div>
                        <h4 class="text-lg font-bold text-gray-900 dark:text-white mb-2">${escapeHtml(item.title)}</h4>
                        <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-4">${escapeHtml(item.description)}</p>
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-600 border-t border-gray-200 dark:border-gray-800 pt-3 flex justify-between items-center">
                        <span class="font-mono text-indigo-600 dark:text-indigo-400 font-semibold">${shortId}</span>
                        <span class="text-gray-500">In DB gespeichert</span>
                    </div>
                `;
                itemsGrid.appendChild(card);
            });
        } catch (error) {
            console.error("Fehler beim Laden:", error);
        }
    }

    // ---------------------------------------------------------------
    // FORMULAR ABSENDEN
    // ---------------------------------------------------------------
    async function handleFormSubmit(event) {
        event.preventDefault();
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        submitBtn.innerText = "⏳ KI-Matching läuft...";

        const selectedCategory = document.querySelector('input[name="category"]:checked')?.value || 'Sonstiges';

        let title = itemTitleInput.value;
        let description = itemDescription.value;

        if (currentMode === 'simple') {
            // Kein Modell bekannt: Titel = Kategorie, Farbe/Hülle werden
            // an die Beschreibung angehängt, damit die KI sie mitbekommt.
            title = selectedColor ? `${selectedCategory} (${selectedColor})` : selectedCategory;
            const extras = [];
            if (selectedColor) extras.push(`Farbe: ${selectedColor}`);
            if (selectedCase) extras.push(`Hülle/Zustand: ${selectedCase}`);
            if (extras.length > 0) {
                description = description ? `${description}\n${extras.join(', ')}` : extras.join(', ');
            }
        }

        if (!title) title = selectedCategory;
        if (!description) {
            alert("Bitte gib noch eine kurze Beschreibung an.");
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            submitBtn.innerText = "Meldung absenden & KI-Matching starten";
            return;
        }

        const payload = {
            type: itemTypeInput.value,
            category: selectedCategory,
            title: title,
            description: description,
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