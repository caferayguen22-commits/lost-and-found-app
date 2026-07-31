import { dom } from './dom.js';
import { state } from './state.js';

export function createChip(label, onClick) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'chip-btn px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 hover:border-indigo-400 text-gray-700 dark:text-gray-300 transition-all';
    btn.innerText = label;
    btn.addEventListener('click', onClick);
    return btn;
}

export function setActiveChip(container, activeBtn) {
    container.querySelectorAll('.chip-btn').forEach(b => {
        b.classList.remove('border-indigo-500', 'bg-indigo-100', 'dark:bg-indigo-950/40', 'text-gray-900', 'dark:text-white');
    });
    activeBtn.classList.add('border-indigo-500', 'bg-indigo-100', 'dark:bg-indigo-950/40', 'text-gray-900', 'dark:text-white');
}

export function setMode(mode) {
    state.currentMode = mode;
    const activeClasses = ['border-indigo-500', 'bg-indigo-100', 'dark:bg-indigo-950/30', 'text-gray-900', 'dark:text-white'];
    const inactiveClasses = ['border-gray-200', 'dark:border-gray-800', 'bg-gray-100', 'dark:bg-gray-950', 'text-gray-600', 'dark:text-gray-300'];

    [dom.modeExpertBtn, dom.modeSimpleBtn].forEach(btn => {
        btn.classList.remove(...activeClasses, ...inactiveClasses);
    });

    if (mode === 'expert') {
        dom.modeExpertBtn.classList.add(...activeClasses);
        dom.modeSimpleBtn.classList.add(...inactiveClasses);
        dom.expertModeContainer.classList.remove('hidden');
        dom.simpleModeContainer.classList.add('hidden');
    } else {
        dom.modeSimpleBtn.classList.add(...activeClasses);
        dom.modeExpertBtn.classList.add(...inactiveClasses);
        dom.expertModeContainer.classList.add('hidden');
        dom.simpleModeContainer.classList.remove('hidden');
        const category = document.querySelector('input[name="category"]:checked')?.value || 'Sonstiges';
        renderSimpleMode(category);
    }
}

export function updateCategoryUI(category) {
    dom.brandButtonsDiv.innerHTML = '';
    dom.seriesChipsDiv.innerHTML = '';
    dom.variantChipsDiv.innerHTML = '';
    dom.seriesContainer.classList.add('hidden');
    dom.variantContainer.classList.add('hidden');
    dom.itemTitleInput.value = '';

    const brandsForCategory = state.productDB[category];

    if (brandsForCategory) {
        dom.modeToggleContainer.classList.remove('hidden');
        dom.brandContainer.classList.remove('hidden');
        Object.keys(brandsForCategory).forEach(brand => {
            const btn = createChip(brand, () => {
                setActiveChip(dom.brandButtonsDiv, btn);
                renderSeries(category, brand);
            });
            dom.brandButtonsDiv.appendChild(btn);
        });
    } else {
        dom.modeToggleContainer.classList.add('hidden');
        dom.brandContainer.classList.add('hidden');
        setMode('expert');
    }

    if (state.caseOptionsByCategory[category]) {
        dom.caseSelectionContainer.classList.remove('hidden');
        dom.caseLabel.textContent = state.caseOptionsByCategory[category].label;
    } else {
        dom.caseSelectionContainer.classList.add('hidden');
    }

    if (state.currentMode === 'simple') {
        renderSimpleMode(category);
    }

    if (category === 'Kopfhörer') {
        dom.safetyTipText.innerText = 'Tipp: Ladecase oder In-Ear einzeln verloren? Erwähne es in der Beschreibung!';
    } else if (category === 'Schlüssel') {
        dom.safetyTipText.innerText = 'Tipp: Gib niemals deine genaue Wohnadresse als Fund/Verlustort bei Schlüsseln an!';
    } else {
        dom.safetyTipText.innerText = 'Tipp für die Übergabe: Verabredet euch an einem belebten, öffentlichen Ort.';
    }
}

export function renderSeries(category, brand) {
    dom.seriesChipsDiv.innerHTML = '';
    dom.variantChipsDiv.innerHTML = '';
    dom.variantContainer.classList.add('hidden');
    dom.itemTitleInput.value = '';

    const seriesMap = state.productDB[category]?.[brand] || {};
    const seriesNames = Object.keys(seriesMap);

    if (seriesNames.length === 0) {
        dom.seriesContainer.classList.add('hidden');
        dom.itemTitleInput.placeholder = `Modell von ${brand} hier eintragen...`;
        dom.itemTitleInput.focus();
        return;
    }

    dom.seriesContainer.classList.remove('hidden');
    seriesNames.forEach(serie => {
        const btn = createChip(serie, () => {
            setActiveChip(dom.seriesChipsDiv, btn);
            renderVariants(seriesMap[serie]);
        });
        dom.seriesChipsDiv.appendChild(btn);
    });
}

export function renderVariants(variants) {
    dom.variantChipsDiv.innerHTML = '';

    if (variants.length <= 1) {
        dom.variantContainer.classList.add('hidden');
        dom.itemTitleInput.value = variants[0] || '';
        return;
    }

    dom.variantContainer.classList.remove('hidden');
    dom.itemTitleInput.value = '';
    dom.itemTitleInput.placeholder = 'Variante oben wählen oder hier tippen...';
    variants.forEach(variant => {
        const btn = createChip(variant, () => {
            setActiveChip(dom.variantChipsDiv, btn);
            dom.itemTitleInput.value = variant;
        });
        dom.variantChipsDiv.appendChild(btn);
    });
}

export function renderSimpleMode(category) {
    dom.colorChipsDiv.innerHTML = '';
    dom.caseChipsDiv.innerHTML = '';
    state.selectedColor = null;
    state.selectedCase = null;

    state.colorOptions.forEach(color => {
        const btn = createChip(color, () => {
            setActiveChip(dom.colorChipsDiv, btn);
            state.selectedColor = color;
        });
        dom.colorChipsDiv.appendChild(btn);
    });

    const caseConfig = state.caseOptionsByCategory[category];
    if (caseConfig) {
        caseConfig.options.forEach(opt => {
            const btn = createChip(opt, () => {
                setActiveChip(dom.caseChipsDiv, btn);
                state.selectedCase = opt;
            });
            dom.caseChipsDiv.appendChild(btn);
        });
    }
}