document.addEventListener('DOMContentLoaded', () => {
    // DOM Elemente selektieren
    const btnLost = document.getElementById('btn-lost');
    const btnFound = document.getElementById('btn-found');
    const btnBack = document.getElementById('btn-back');
    const btnReset = document.getElementById('btn-reset');

    const formContainer = document.getElementById('form-container');
    const resultContainer = document.getElementById('result-container');
    const itemForm = document.getElementById('item-form');
    const submitBtn = document.getElementById('submit-btn');

    const itemTypeInput = document.getElementById('item-type');
    const formTitle = document.getElementById('form-title');
    const hintBox = document.getElementById('hint-box');
    const resultContent = document.getElementById('result-content');

    // Event Listener für Typ-Auswahl
    btnLost.addEventListener('click', () => openForm('lost'));
    btnFound.addEventListener('click', () => openForm('found'));
    btnBack.addEventListener('click', resetUI);
    btnReset.addEventListener('click', resetUI);
    itemForm.addEventListener('submit', handleFormSubmit);

    function openForm(type) {
        itemTypeInput.value = type;
        formContainer.classList.remove('hidden');
        resultContainer.classList.add('hidden');

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
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async function handleFormSubmit(event) {
        event.preventDefault();

        submitBtn.disabled = true;
        submitBtn.innerText = "Analyse läuft... Bitte warten...";

        const payload = {
            type: itemTypeInput.value,
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
                resultContent.innerText = data.ai_report;
                resultContainer.scrollIntoView({ behavior: 'smooth' });
            } else {
                alert("Fehler: " + (data.message || "Meldung konnte nicht angelegt werden."));
            }
        } catch (error) {
            alert("Verbindungsfehler zum Server.");
            console.error(error);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = "Meldung absenden & KI-Matching starten";
        }
    }
});