import { dom } from './dom.js';
import { state } from './state.js';
import { setMode, updateCategoryUI } from './chip-ui.js';

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
        dom.secretFeatureContainer.classList.remove('hidden');
    } else {
        dom.formTitle.innerText = "Verlustmeldung aufgeben";
        dom.hintBox.innerText = "Beschreibe deinen Gegenstand so genau wie möglich. Unsere KI durchsucht sofort alle Meldungen.";
        dom.secretFeatureContainer.classList.add('hidden');
    }
    dom.formContainer.scrollIntoView({ behavior: 'smooth' });
}

export function resetUI() {
    dom.formContainer.classList.add('hidden');
    dom.resultContainer.classList.add('hidden');
    dom.itemForm.reset();
    state.base64Image = "";
    dom.descriptionSuggestionContainer.classList.add('hidden');
    dom.descriptionSuggestionConfirmation.classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showDescriptionSuggestion(itemId, correctedDescription) {
    dom.descriptionSuggestionText.innerText = correctedDescription;
    dom.descriptionSuggestionConfirmation.classList.add('hidden');
    dom.descriptionSuggestionContainer.classList.remove('hidden');

    // .onclick statt addEventListener -- überschreibt bei jeder neuen Meldung
    // sauber den vorherigen Handler, statt sich über mehrere Submits hinweg
    // aufzustapeln (das Formular bleibt ja über mehrere Meldungen im DOM).
    dom.btnAcceptSuggestion.onclick = async () => {
        dom.btnAcceptSuggestion.disabled = true;
        dom.btnRejectSuggestion.disabled = true;
        try {
            const response = await fetch(`/api/items/${itemId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ description: correctedDescription })
            });
            if (response.ok) {
                dom.descriptionSuggestionConfirmation.innerText = "✅ Übernommen -- deine Beschreibung wurde aktualisiert.";
                dom.descriptionSuggestionConfirmation.classList.remove('hidden');
                dom.btnAcceptSuggestion.classList.add('hidden');
                dom.btnRejectSuggestion.classList.add('hidden');
            } else {
                alert("Die Korrektur konnte nicht übernommen werden.");
                dom.btnAcceptSuggestion.disabled = false;
                dom.btnRejectSuggestion.disabled = false;
            }
        } catch (error) {
            alert("Verbindungsfehler zum Server.");
            console.error(error);
            dom.btnAcceptSuggestion.disabled = false;
            dom.btnRejectSuggestion.disabled = false;
        }
    };

    dom.btnRejectSuggestion.onclick = () => {
        dom.descriptionSuggestionContainer.classList.add('hidden');
    };
}

export async function handleFormSubmit(event) {
    event.preventDefault();
    if (dom.submitBtn.disabled) return;
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
        email: dom.itemEmailInput.value || null,
        image: state.base64Image
    };

    const currentLocation = dom.itemCurrentLocationInput.value.trim();
    if (currentLocation) {
        payload.current_location = currentLocation;
    }

    // Geheimes Merkmal ist ausschließlich bei Fundmeldungen sinnvoll -- auch
    // wenn das Feld aus irgendeinem Grund sichtbar wäre, wird es bei einer
    // Verlustmeldung nie ins Payload aufgenommen.
    if (payload.type === 'found') {
        const secretFeature = dom.itemSecretFeatureInput.value.trim();
        if (secretFeature) {
            payload.secret_feature = secretFeature;
        }
    }

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

            let resultText = `✅ MELDUNG ERFOLGREICH ERFASST!\n--------------------------------------------------\n`;
            resultText += `Deine Wartemarke: ${data.tracking_code}\n(merke sie dir gut, damit du den Status später abrufen kannst)\n\n`;
            resultText += data.ai_summary || '';
            if (data.match_found) {
                resultText += `\n\n🎉 Möglicher Match gefunden! (${data.match_probability}% Wahrscheinlichkeit)`;
            }
            if (data.recommended_station) {
                resultText += `\n\nEmpfohlene Abgabestation: ${data.recommended_station}`;
            }

            dom.resultContent.innerText = resultText;

            // Rechtschreib-/Grammatik-Vorschlag: nur wenn tatsächlich einer da ist.
            dom.descriptionSuggestionContainer.classList.add('hidden');
            if (data.corrected_description) {
                showDescriptionSuggestion(data.id, data.corrected_description);
            }

            // Bei erfolglosem Match gezielt die Gegenliste anbieten
            dom.browseSuggestionContainer.innerHTML = '';
            dom.browseSuggestionContainer.classList.add('hidden');
            if (!data.match_found) {
                const browseType = payload.type === 'lost' ? 'found' : 'lost';
                const browseLink = document.createElement('a');
                browseLink.href = `/durchsuchen?type=${encodeURIComponent(browseType)}&category=${encodeURIComponent(payload.category)}`;
                browseLink.className = 'block text-center w-full py-3 bg-indigo-50 dark:bg-indigo-950/30 hover:bg-indigo-100 dark:hover:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-800/40 text-indigo-700 dark:text-indigo-300 font-semibold rounded-xl transition-all';
                browseLink.innerText = `🔍 Gemeldete ${payload.category} durchsuchen`;
                dom.browseSuggestionContainer.appendChild(browseLink);
                dom.browseSuggestionContainer.classList.remove('hidden');
            }

            dom.resultContainer.scrollIntoView({ behavior: 'smooth' });
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