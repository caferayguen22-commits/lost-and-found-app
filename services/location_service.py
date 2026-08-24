import math

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


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Berechnet die Luftlinien-Distanz zwischen zwei Koordinaten in km
    (Haversine-Formel, reines Python -- keine KI, kein API-Call).
    """
    EARTH_RADIUS_KM = 6371.0

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


# Zum isolierten Testen: einfach diese Datei direkt in PyCharm ausführen.
if __name__ == "__main__":
    test_result = geocode_berlin_address("Erich-Weinert-Straße 32")
    print(test_result)