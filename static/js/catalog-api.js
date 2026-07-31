import { state } from './state.js';

export async function loadProductCatalog() {
    try {
        const response = await fetch('/api/product-catalog');
        const data = await response.json();
        state.productDB = data.brands;
        state.colorOptions = data.colors;
        state.caseOptionsByCategory = data.cases;
    } catch (error) {
        console.error("Produktkatalog konnte nicht geladen werden:", error);
    }
}