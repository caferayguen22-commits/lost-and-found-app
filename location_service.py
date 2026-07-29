import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Nominatim verlangt einen ehrlichen User-Agent -- keine Ausrede, keine Fantasie-Adresse.
HEADERS = {
    "User-Agent": "LostAndFoundBerlin/1.0 (Studienprojekt)"
}


def geocode_berlin_address(address_query: str) -> dict | None:
    """
    Fragt die kostenlose OpenStreetMap-Nominatim-API nach einer Adresse
    in Berlin und gibt ECHTE Standortdaten zurück (keine KI-Erfindung).
    Gibt None zurück, wenn nichts gefunden wurde.
    """
    params = {
        "q": f"{address_query}, Berlin, Germany",
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=5)
        response.raise_for_status()
        results = response.json()

        if not results:
            return None

        best_match = results[0]
        address_parts = best_match.get("address", {})

        return {
            "full_address": best_match.get("display_name"),
            "lat": float(best_match["lat"]),
            "lon": float(best_match["lon"]),
            "postcode": address_parts.get("postcode"),
            "district": address_parts.get("suburb") or address_parts.get("city_district"),
            "road": address_parts.get("road"),
            "house_number": address_parts.get("house_number")
        }

    except requests.RequestException as e:
        print(f"[WARNUNG] Geocoding fehlgeschlagen: {e}")
        return None


# Zum isolierten Testen: einfach diese Datei direkt in PyCharm ausführen.
if __name__ == "__main__":
    test_result = geocode_berlin_address("Erich-Weinert-Straße 32")
    print(test_result)