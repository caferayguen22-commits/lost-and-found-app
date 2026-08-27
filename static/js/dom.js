// Zentrale Sammlung aller benötigten DOM-Elemente.
export const dom = {
    btnLost: document.getElementById('btn-lost'),
    btnFound: document.getElementById('btn-found'),
    btnBack: document.getElementById('btn-back'),
    btnReset: document.getElementById('btn-reset'),

    formContainer: document.getElementById('form-container'),
    resultContainer: document.getElementById('result-container'),
    browseSuggestionContainer: document.getElementById('browse-suggestion-container'),
    itemForm: document.getElementById('item-form'),
    submitBtn: document.getElementById('submit-btn'),

    itemTypeInput: document.getElementById('item-type'),
    itemTitleInput: document.getElementById('item-title'),
    titleFieldContainer: document.getElementById('title-field-container'),
    formTitle: document.getElementById('form-title'),
    hintBox: document.getElementById('hint-box'),
    resultContent: document.getElementById('result-content'),
    itemDescription: document.getElementById('item-description'),

    categoryInputs: document.querySelectorAll('input[name="category"]'),
    safetyTipText: document.getElementById('safety-tip-text'),

    brandContainer: document.getElementById('brand-selection-container'),
    brandButtonsDiv: document.getElementById('brand-buttons'),
    seriesContainer: document.getElementById('series-selection-container'),
    seriesChipsDiv: document.getElementById('series-chips'),
    variantContainer: document.getElementById('variant-selection-container'),
    variantChipsDiv: document.getElementById('variant-chips'),

    expertModeContainer: document.getElementById('expert-mode-container'),
    modeToggleContainer: document.getElementById('mode-toggle-container'),
    modeExpertBtn: document.getElementById('mode-expert-btn'),
    modeSimpleBtn: document.getElementById('mode-simple-btn'),

    colorChipsDiv: document.getElementById('color-chips'),
    caseSelectionContainer: document.getElementById('case-selection-container'),
    caseChipsDiv: document.getElementById('case-chips'),
    caseLabel: document.getElementById('case-label'),

    imageInput: document.getElementById('item-image'),
    themeToggleBtn: document.getElementById('theme-toggle'),
    themeIcon: document.getElementById('theme-icon'),
    itemEmailInput: document.getElementById('item-email'),
    itemCurrentLocationInput: document.getElementById('item-current-location'),
    secretFeatureContainer: document.getElementById('secret-feature-container'),
    itemSecretFeatureInput: document.getElementById('item-secret-feature'),

    descriptionSuggestionContainer: document.getElementById('description-suggestion-container'),
    descriptionSuggestionText: document.getElementById('description-suggestion-text'),
    btnAcceptSuggestion: document.getElementById('btn-accept-suggestion'),
    btnRejectSuggestion: document.getElementById('btn-reject-suggestion'),
    descriptionSuggestionConfirmation: document.getElementById('description-suggestion-confirmation')
};