import { dom } from './dom.js';
import { state } from './state.js';
import { setMode, updateCategoryUI } from './chip-ui.js';
import { initPhotoAnalysis } from './photo-analysis.js';

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

// Kategorien, die praktisch immer als "hochwertig" gelten -- Smartphone/
// Laptop/Tablet wegen des Sachwerts, Geldbörse wegen möglichem Bargeld/
// Ausweisdokumenten (genau die Fälle, bei denen auch das echte Fundrecht/
// Fundbüro eine Abgabe bei der Polizei empfiehlt). Zusätzlich lässt sich
// ein optionaler geschätzter Wert eintragen -- rein clientseitig, wird NICHT
// an den Server geschickt, dient nur als zweiter Trigger für den Hinweis.
const VALUE_ALERT_CATEGORIES = ['Smartphone', 'Laptop/Tablet', 'Geldbörse'];
const VALUE_ALERT_THRESHOLD_EUR = 150;

export function updateValuableItemHint() {
    if (dom.itemTypeInput.value !== 'found') {
        dom.valuableItemHint.classList.add('hidden');
        return;
    }
    const category = document.querySelector('input[name="category"]:checked')?.value;
    const value = parseFloat(dom.itemEstimatedValueInput.value);
    const isValuable = VALUE_ALERT_CATEGORIES.includes(category) || (!isNaN(value) && value >= VALUE_ALERT_THRESHOLD_EUR);
    dom.valuableItemHint.classList.toggle('hidden', !isValuable);
}

// Debounce, damit nicht bei jedem einzelnen Tastenanschlag ein Request
// rausgeht -- die Prüfung selbst ist zwar billig (rein lokal, kein KI-
// Aufruf), aber ein Request pro Zeichen wäre trotzdem unnötig.
let overlapCheckTimer = null;

export function checkSecretFeatureOverlap() {
    if (dom.itemTypeInput.value !== 'found') {
        dom.secretFeatureOverlapWarning.classList.add('hidden');
        return;
    }
    clearTimeout(overlapCheckTimer);
    overlapCheckTimer = setTimeout(async () => {
        const secretFeature = dom.itemSecretFeatureInput.value.trim();
        const description = dom.itemDescription.value.trim();
        if (!secretFeature || !description) {
            dom.secretFeatureOverlapWarning.classList.add('hidden');
            return;
        }
        try {
            const response = await fetch('/api/check-secret-feature-overlap', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ secret_feature: secretFeature, description })
            });
            const data = await response.json();
            dom.secretFeatureOverlapWarning.classList.toggle('hidden', !(response.ok && data.overlap));
        } catch (error) {
            // Reiner Hinweis, kein kritischer Pfad -- bei Verbindungsfehler
            // einfach nichts anzeigen, statt den Nutzer zu stören.
            console.error(error);
        }
    }, 500);
}

export function initPhotoAnalysisForItemForm() {
    initPhotoAnalysis({
        analyzeBtn: dom.photoAnalyzeBtn,
        guidanceBox: dom.photoGuidanceBox,
        guidanceText: dom.photoGuidanceText,
        suggestionBox: dom.photoSuggestionBox,
        suggestionDetailsText: dom.photoSuggestionDetails,
        suggestionTitleText: dom.photoSuggestionTitle,
        suggestionDescriptionText: dom.photoSuggestionDescription,
        acceptBtn: dom.btnAcceptPhotoSuggestion,
        rejectBtn: dom.btnRejectPhotoSuggestion,
        getBase64Image: () => state.base64Image,
        getCategory: () => document.querySelector('input[name="category"]:checked')?.value,
        onAccept: (result) => {
            if (result.suggested_title) dom.itemTitleInput.value = result.suggested_title;
            if (result.suggested_description) dom.itemDescription.value = result.suggested_description;
        }
    });
}

export function openForm(type) {
    dom.itemForm.reset();
    state.base64Image = "";
    dom.itemTypeInput.value = type;
    dom.formContainer.classList.remove('hidden');
    dom.resultContainer.classList.add('hidden');
    dom.photoGuidanceBox.classList.add('hidden');
    dom.photoSuggestionBox.classList.add('hidden');

    const defaultCategory = document.querySelector('input[name="category"]:checked')?.value || 'Smartphone';
    setMode('expert');
    updateCategoryUI(defaultCategory);

    if (type === 'found') {
        dom.formTitle.innerText = "Fundgegenstand erfassen";
        dom.hintBox.innerText = "Danke für deine Ehrlichkeit! Präzise Details erhöhen die Chance extrem, den Eigentümer sofort zu finden.";
        dom.secretFeatureContainer.classList.remove('hidden');
        dom.valuableItemContainer.classList.remove('hidden');
        dom.descriptionSecretHint.classList.remove('hidden');
    } else {
        dom.formTitle.innerText = "Verlustmeldung aufgeben";
        dom.hintBox.innerText = "Beschreibe deinen Gegenstand so genau wie möglich. Unsere KI durchsucht sofort alle Meldungen.";
        dom.secretFeatureContainer.classList.add('hidden');
        dom.valuableItemContainer.classList.add('hidden');
        dom.descriptionSecretHint.classList.add('hidden');
    }
    updateValuableItemHint();
    dom.secretFeatureOverlapWarning.classList.add('hidden');
    dom.formContainer.scrollIntoView({ behavior: 'smooth' });
}

export function resetUI() {
    dom.formContainer.classList.add('hidden');
    dom.resultContainer.classList.add('hidden');
    dom.itemForm.reset();
    state.base64Image = "";
    dom.descriptionSuggestionContainer.classList.add('hidden');
    dom.descriptionSuggestionConfirmation.classList.add('hidden');
    dom.photoGuidanceBox.classList.add('hidden');
    dom.photoSuggestionBox.classList.add('hidden');
    dom.valuableItemHint.classList.add('hidden');
    dom.secretFeatureOverlapWarning.classList.add('hidden');
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
            if (!dom.itemSecretFeatureConfirm.checked) {
                alert('Bitte bestätige zuerst per Checkbox, dass das geheime Merkmal auf dem Foto nicht sichtbar ist und in der Beschreibung nicht erwähnt wird.');
                dom.submitBtn.disabled = false;
                dom.submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                dom.submitBtn.innerText = "Meldung absenden & KI-Matching starten";
                return;
            }
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
                const station = data.recommended_station;
                let stationText = `${station.name} (${station.address}, ${station.district})`;
                if (station.distance_km !== null && station.distance_km !== undefined) {
                    stationText += ` -- ca. ${station.distance_km} km entfernt`;
                }
                resultText += `\n\nEmpfohlene Abgabestation: ${stationText}`;
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