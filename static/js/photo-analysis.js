// Gemeinsames Modul für die Foto-Analyse (Schritt A: Ausreichend-Check,
// Schritt B: Vorschlag) -- wird sowohl von main.js (Verlust- UND
// Fund-Formular, teilen sich dasselbe Formular) als auch von garage.js
// genutzt, damit der Ablauf nicht dreimal dupliziert wird.
//
// Aufruf-Pattern bewusst wie bei der bestehenden Rechtschreib-Vorschlagsbox
// (siehe form.js showDescriptionSuggestion): ein Vorschlag, zwei Buttons
// (Übernehmen/Verwerfen), kein automatisches Überschreiben.

// Gleiche Liste wie SUPPORTED_IMAGE_TYPES in services/photo_analysis_service.py
// -- hier nur als schnelle Vorabprüfung, damit ein bekannt nicht unterstütztes
// Format (v.a. HEIC vom iPhone) gar nicht erst einen Request auslöst. Die
// eigentliche, verbindliche Prüfung bleibt serverseitig.
const SUPPORTED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];

function getMimeType(dataUrl) {
    const match = /^data:([^;]+);base64,/i.exec(dataUrl || '');
    return match ? match[1].toLowerCase() : null;
}

function buildDetailsText(result) {
    const parts = [];
    if (result.brand) parts.push(`Marke: ${result.brand}`);
    if (result.model) parts.push(`Modell: ${result.model}`);
    if (result.color) parts.push(`Farbe: ${result.color}`);
    if (result.other_features) parts.push(`Sonstiges: ${result.other_features}`);
    if (result.condition_description) parts.push(`Zustand: ${result.condition_description}`);
    return parts.join(' · ');
}

/**
 * @param {Object} config
 * @param {HTMLElement} config.analyzeBtn - Button "Foto analysieren"
 * @param {HTMLElement} config.guidanceBox - Container für den Schritt-A-Hinweis
 * @param {HTMLElement} config.guidanceText - Textelement innerhalb der Hinweisbox
 * @param {HTMLElement} config.suggestionBox - Container für die Schritt-B-Vorschlagsbox
 * @param {HTMLElement} config.suggestionDetailsText - Textelement für Marke/Modell/Farbe/Zustand
 * @param {HTMLElement} config.suggestionTitleText - Textelement für den Titel-Vorschlag
 * @param {HTMLElement} config.suggestionDescriptionText - Textelement für den Beschreibungs-Vorschlag
 * @param {HTMLElement} config.acceptBtn - Button "Übernehmen"
 * @param {HTMLElement} config.rejectBtn - Button "Verwerfen"
 * @param {() => string} config.getBase64Image - liefert das aktuell gewählte Foto als Base64-Data-URL
 * @param {() => string} config.getCategory - liefert die aktuell gewählte/eingegebene Kategorie
 * @param {(result: Object) => void} config.onAccept - befüllt Titel/Beschreibung im jeweiligen Formular
 */
export function initPhotoAnalysis(config) {
    const {
        analyzeBtn, guidanceBox, guidanceText, suggestionBox,
        suggestionDetailsText, suggestionTitleText, suggestionDescriptionText,
        acceptBtn, rejectBtn, getBase64Image, getCategory, onAccept
    } = config;

    function resetBoxes() {
        guidanceBox.classList.add('hidden');
        suggestionBox.classList.add('hidden');
    }

    analyzeBtn.addEventListener('click', async () => {
        const image = getBase64Image();
        if (!image) {
            alert('Bitte zuerst ein Foto auswählen.');
            return;
        }

        const mimeType = getMimeType(image);
        if (mimeType && !SUPPORTED_IMAGE_TYPES.includes(mimeType)) {
            alert(
                `Dieses Bildformat (${mimeType}) wird von der Foto-Analyse leider nicht unterstützt -- ` +
                'häufig bei HEIC-Fotos vom iPhone. Bitte wähle ein JPEG- oder PNG-Foto (z.B. beim ' +
                "Teilen/Exportieren 'Als JPEG' wählen, oder einen Screenshot des Fotos hochladen)."
            );
            return;
        }

        resetBoxes();
        analyzeBtn.disabled = true;
        const originalText = analyzeBtn.innerText;
        analyzeBtn.innerText = '⏳ Foto wird analysiert...';

        try {
            const response = await fetch('/api/analyze-photo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image, category: getCategory() || null })
            });
            const data = await response.json();

            if (!response.ok) {
                alert('Fehler: ' + (data.message || 'Foto-Analyse fehlgeschlagen.'));
                return;
            }

            if (!data.sufficient_detail) {
                guidanceText.innerText = data.guidance_hint || 'Auf dem Foto sind leider nicht genug Details erkennbar. Du kannst trotzdem ohne weiteres Foto fortfahren.';
                guidanceBox.classList.remove('hidden');
                return;
            }

            suggestionDetailsText.innerText = buildDetailsText(data) || '(keine weiteren Details erkannt)';
            suggestionTitleText.innerText = data.suggested_title || '(kein Titel-Vorschlag)';
            suggestionDescriptionText.innerText = data.suggested_description || '(kein Beschreibungs-Vorschlag)';
            suggestionBox.classList.remove('hidden');

            // .onclick statt addEventListener -- überschreibt bei jeder neuen
            // Analyse sauber den vorherigen Handler.
            acceptBtn.onclick = () => {
                onAccept(data);
                suggestionBox.classList.add('hidden');
            };
            rejectBtn.onclick = () => {
                suggestionBox.classList.add('hidden');
            };
        } catch (error) {
            alert('Verbindungsfehler zum Server.');
            console.error(error);
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.innerText = originalText;
        }
    });
}
