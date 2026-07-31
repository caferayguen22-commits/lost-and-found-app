// Zentraler, gemeinsam genutzter Zustand für alle Module.
export const state = {
    base64Image: "",
    currentMode: 'expert', // 'expert' | 'simple'
    selectedColor: null,
    selectedCase: null,
    productDB: {},
    colorOptions: [],
    caseOptionsByCategory: {}
};