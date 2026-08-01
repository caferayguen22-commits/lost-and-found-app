import { dom } from './dom.js';
import { state } from './state.js';
import { setMode, updateCategoryUI } from './chip-ui.js';
import { loadDashboardItems } from './dashboard.js';

export function initImageInput() {
    if (dom.imageInput) {
        dom.imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onloadend = () => { state.base64Image = reader.result; };
                reader.readAsDataURL(file);
            }
        });
    }
}

export function openForm(type) {
    dom.itemForm.reset();
    state.base64Image = "";
    dom.itemTypeInput.value = type;
    dom.formContainer.classList.remove('hidden');
    dom.resultContainer.classList.add('hidden');

    const defaultCategory = document.querySelector('input[name="category"]:checked')?.value || 'Smartphone';
    setMode('expert');
    updateCategoryUI(defaultCategory);

    if (type === 'found') {
        dom.formTitle.innerText = "Fundgegenstand erfassen";
        dom.hintBox.innerText = "Danke für deine Ehrlichkeit! Präzise Details erhöhen die Chance extrem, den Eigentümer sofort zu finden.";
    } else {
        dom.formTitle.innerText = "Verlustmeldung aufgeben";
        dom.hintBox.innerText = "Beschreibe deinen Gegenstand so genau wie möglich. Unsere KI durchsucht sofort alle Meldungen.";
    }
    dom.formContainer.scrollIntoView({ behavior: 'smooth' });
}

export function resetUI() {
    dom.formContainer.classList.add('hidden');
    dom.resultContainer.classList.add('hidden');
    dom.itemForm.reset();
    state.base64Image = "";
    loadDashboardItems();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

export async function handleFormSubmit(event) {
    event.preventDefault();
    dom.submitBtn.disabled = true;
    dom.submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
    dom.submitBtn.innerText = "⏳ KI-Matching läuft...";

    const selectedCategory = document.querySelector('input[name="category"]:checked')?.value || 'Sonstiges';

    let title = dom.itemTitleInput.value;
    let description = dom.itemDescription.value;

    if (state.currentMode === 'simple') {
        title = state.selectedColor ? `${selectedCategory} (${state.selectedColor})` : selectedCategory;
        const extras = [];
        if (state.selectedColor) extras.push(`Farbe: ${state.selectedColor}`);
        if (state.selectedCase) extras.push(`Hülle/Zustand: ${state.selectedCase}`);
        if (extras.length > 0) {
            description = description ? `${description}\n${extras.join(', ')}` : extras.join(', ');
        }
    }

    if (!title) title = selectedCategory;
    if (!description) {
        alert("Bitte gib noch eine kurze Beschreibung an.");
        dom.submitBtn.disabled = false;
        dom.submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        dom.submitBtn.innerText = "Meldung absenden & KI-Matching starten";
        return;
    }

    const payload = {
        type: dom.itemTypeInput.value,
        category: selectedCategory,
        title: title,
        description: description,
        location: document.getElementById('item-location').value,
        image: state.base64Image
    };

    try {
        const response = await fetch('/api/items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (response.ok) {
            dom.formContainer.classList.add('hidden');
            dom.resultContainer.classList.remove('hidden');
            dom.resultContent.innerText = `✅ MELDUNG ERFOLGREICH ERFASST!\n--------------------------------------------------\n` + data.ai_report;
            dom.resultContainer.scrollIntoView({ behavior: 'smooth' });
            loadDashboardItems();
        } else {
            alert("Fehler: " + (data.message || "Meldung konnte nicht angelegt werden."));
        }
    } catch (error) {
        alert("Verbindungsfehler zum Server.");
        console.error(error);
    } finally {
        dom.submitBtn.disabled = false;
        dom.submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        dom.submitBtn.innerText = "Meldung absenden & KI-Matching starten";
    }
}