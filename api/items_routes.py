import json
import secrets

from flask import Blueprint, jsonify, request, render_template
from openai import OpenAIError

from services.db import openai_client
from services.items_repository import (
    insert_item, get_item_by_id, get_all_items, get_items_by_type_and_category,
    update_item as update_item_row, delete_item as delete_item_row, mark_matched
)
from services.stations_repository import get_stations_by_category, get_station_by_name
from services.location_service import geocode_berlin_address, haversine_distance_km
from services.prompt_service import build_found_prompt, build_lost_prompt
from services.product_catalog import PRODUCT_DB, COLOR_OPTIONS, CASE_OPTIONS_BY_CATEGORY
from services.email_service import send_match_notification
from models.item import Item

items_bp = Blueprint('items', __name__)


def normalize_category(cat: str) -> str:
    """Normalisiert Freitext-Eingaben auf vordefinierte Hauptkategorien."""
    if not cat:
        return 'Sonstiges'
    cat_lower = str(cat).lower()

    if any(k in cat_lower for k in ['handy', 'phone', 'mobil', 'smartphone', 'iphone', 'samsung', 'xiaomi', 'pixel']):
        return 'Smartphone'
    if any(k in cat_lower for k in ['schlüssel', 'key', 'bund']):
        return 'Schlüssel'
    if any(k in cat_lower for k in ['geldbörse', 'portemonnaie', 'börse', 'wallet']):
        return 'Geldbörse'

    return cat


def generate_tracking_code():
    return secrets.token_hex(3).upper()  # z.B. 'A1B2C3'


GENERAL_STATION_CATEGORY = "Straße / Sonstiges"


def find_recommended_station(category, origin=None):
    """
    Deterministische Stationsempfehlung -- keine KI, keine Halluzination.
    Sind in `origin` (dict mit 'lat'/'lon') Koordinaten vorhanden, wird unter
    den passenden Kandidaten per Haversine-Formel (reines Python) die wirklich
    nächstgelegene Station berechnet:
    1. bevorzugt unter Stationen, die exakt `category` bedienen
    2. sonst unter den allgemeinen "Straße / Sonstiges"-Stationen
       (kategorie-spezifische Stationen wie das BVG-Zentralfundbüro sind
       sonst fälschlich auch für ungeeignete Funde die "nächste" Station)
    Ohne nutzbare Koordinaten greift die bisherige, rein kategoriebasierte
    Auswahl als Fallback.
    Gibt (Station | None, distance_km | None) zurück.
    """
    if origin and origin.get('lat') is not None and origin.get('lon') is not None:
        candidates = get_stations_by_category(category, only_with_coords=True)
        if not candidates:
            candidates = get_stations_by_category(GENERAL_STATION_CATEGORY, only_with_coords=True)

        if candidates:
            nearest = min(
                candidates,
                key=lambda s: haversine_distance_km(origin['lat'], origin['lon'], s.lat, s.lon)
            )
            distance_km = round(haversine_distance_km(origin['lat'], origin['lon'], nearest.lat, nearest.lon), 1)
            return nearest, distance_km

    # Fallback ohne nutzbare Koordinaten: bisherige rein kategoriebasierte Auswahl
    category_matches = get_stations_by_category(category)
    station = category_matches[0] if category_matches else get_station_by_name("Zentrales Fundbüro Berlin")
    return (station, None) if station else (None, None)


@items_bp.route('/')
def home():
    return render_template('index.html')


@items_bp.route('/durchsuchen')
def durchsuchen():
    return render_template('durchsuchen.html')


@items_bp.route('/api/product-catalog', methods=['GET'])
def get_product_catalog():
    return jsonify({
        "brands": PRODUCT_DB,
        "colors": COLOR_OPTIONS,
        "cases": CASE_OPTIONS_BY_CATEGORY
    }), 200


@items_bp.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "Keine Daten übergeben."}), 400

    item_type = data.get('type')
    if item_type not in ['lost', 'found']:
        return jsonify({"status": "error", "message": "Ungültiger Typ ('lost' oder 'found')."}), 400

    raw_category = data.get('category', 'Sonstiges')
    category = normalize_category(raw_category)

    title = data.get('title', 'Unbekannter Gegenstand')
    description = data.get('description', 'Keine Beschreibung vorhanden')
    raw_location = data.get('location', 'Kein spezifischer Ort angegeben')
    current_location_input = data.get('current_location')
    current_location = current_location_input or raw_location

    location_data = geocode_berlin_address(raw_location)
    if location_data:
        corrected_location = (
            f"{location_data.get('road') or raw_location} "
            f"{location_data.get('house_number') or ''}, "
            f"{location_data.get('postcode') or ''} Berlin "
            f"({location_data.get('district') or 'Bezirk unbekannt'})"
        ).strip()
    else:
        corrected_location = raw_location

    # Ausgangspunkt für die Distanzberechnung zur Abgabestation: bevorzugt der
    # aktuelle Standort (falls angegeben und geocodierbar), sonst der Fundort.
    if current_location_input:
        distance_origin = geocode_berlin_address(current_location_input) or location_data
    else:
        distance_origin = location_data

    if item_type == 'found':
        user_hint = (
            "Danke, dass du ein ehrlicher Finder bist! Hilf dem suchenden Besitzer, "
            "seinen Gegenstand schnell wiederzufinden: Je genauer du Details beschreibst, "
            "desto sicherer schlägt unser automatisches KI-Matching an."
        )
    else:
        user_hint = (
            "Um die Chancen für ein erfolgreiches Matching zu maximieren, beschreibe "
            "deinen Verlust bitte so präzise wie möglich."
        )

    # --- Bidirektionales Matching: IMMER gegen die jeweils andere Liste prüfen ---
    opposite_type = 'lost' if item_type == 'found' else 'found'
    other_items_list = [
        {
            "id": other.id,
            "title": other.title,
            "description": other.description,
            "location": other.corrected_location or other.location,
        }
        for other in get_items_by_type_and_category(opposite_type, category)
    ]

    parsed_result = {
        "summary": None,
        "match_found": False,
        "matched_item_id": None,
        "match_probability": None,
    }

    try:
        if item_type == 'found':
            system_message, prompt = build_found_prompt(
                category=category,
                title=title,
                description=description,
                corrected_location=corrected_location,
                current_location=current_location,
                other_items_list=other_items_list
            )
        else:
            system_message, prompt = build_lost_prompt(
                category=category,
                title=title,
                description=description,
                corrected_location=corrected_location,
                other_items_list=other_items_list
            )

        ai_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            timeout=15.0,
            response_format={"type": "json_object"}
        )

        parsed_result = json.loads(ai_response.choices[0].message.content)

    except OpenAIError as oe:
        parsed_result["summary"] = f"KI-Bericht derzeit nicht verfügbar (OpenAI API Fehler: {str(oe)})."
    except json.JSONDecodeError:
        parsed_result["summary"] = "KI-Antwort konnte nicht als JSON verarbeitet werden."
    except Exception as e:
        parsed_result["summary"] = f"KI-Bericht konnte nicht generiert werden: {str(e)}"

    recommended_station, distance_km = (None, None)
    if item_type == 'found':
        recommended_station, distance_km = find_recommended_station(category, origin=distance_origin)

    item = Item(
        type=item_type,
        category=category,
        title=title,
        description=description,
        location=raw_location,
        corrected_location=corrected_location,
        tracking_code=generate_tracking_code(),
        user_hint=user_hint,
        location_lat=location_data.get('lat') if location_data else None,
        location_lon=location_data.get('lon') if location_data else None,
        location_postcode=location_data.get('postcode') if location_data else None,
        location_district=location_data.get('district') if location_data else None,
        location_road=location_data.get('road') if location_data else None,
        location_house_number=location_data.get('house_number') if location_data else None,
        current_location=current_location_input,
        email=data.get('email'),
        image=data.get('image'),
        ai_summary=parsed_result.get('summary'),
        recommended_station_id=recommended_station.id if recommended_station else None,
        recommended_station_distance_km=distance_km,
        # Nur bei Fundmeldungen relevant -- entspricht der CHECK-Constraint in services/db.py.
        # Fließt bewusst NIRGENDS in other_items_list oder die KI-Prompts ein.
        secret_feature=(data.get('secret_feature') or None) if item_type == 'found' else None
    )

    matched_item = None
    match_id_raw = parsed_result.get('matched_item_id')
    if parsed_result.get('match_found') and match_id_raw is not None:
        try:
            matched_item = get_item_by_id(int(match_id_raw))
        except (TypeError, ValueError):
            matched_item = None

        if matched_item:
            item.match_found = True
            item.matched_item_id = matched_item.id
            item.match_probability = parsed_result.get('match_probability')
            mark_matched(matched_item.id, parsed_result.get('match_probability'))

    new_item = insert_item(item)

    # E-Mail-Benachrichtigungen an beide Seiten, sofern hinterlegt
    if new_item.match_found:
        if matched_item and matched_item.email:
            send_match_notification(
                to_email=matched_item.email,
                item_title=matched_item.title,
                tracking_code=matched_item.tracking_code,
                match_probability=new_item.match_probability
            )
        if new_item.email:
            send_match_notification(
                to_email=new_item.email,
                item_title=new_item.title,
                tracking_code=new_item.tracking_code,
                match_probability=new_item.match_probability
            )

    recommended_station_payload = None
    if recommended_station:
        recommended_station_payload = {
            "name": recommended_station.name,
            "address": recommended_station.address,
            "district": recommended_station.district,
            "distance_km": distance_km
        }

    return jsonify({
        "status": "success",
        "message": "Meldung erfolgreich angelegt.",
        "id": new_item.id,
        "tracking_code": new_item.tracking_code,
        "ai_summary": new_item.ai_summary,
        "match_found": new_item.match_found,
        "match_probability": new_item.match_probability,
        "recommended_station": recommended_station_payload,
        "hint": new_item.user_hint
    }), 201


@items_bp.route('/api/items', methods=['GET'])
def get_items():
    return jsonify([item.to_dict() for item in get_all_items()]), 200


@items_bp.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    if delete_item_row(item_id):
        return jsonify({"status": "success", "message": "Gegenstand erfolgreich entfernt."}), 200
    return jsonify({"status": "error", "message": "Gegenstand wurde nicht gefunden."}), 404


@items_bp.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Keine Daten übergeben."}), 400

    if update_item_row(item_id, **data):
        return jsonify({"status": "success", "message": "Gegenstand erfolgreich aktualisiert!"}), 200
    return jsonify({"status": "error", "message": "Gegenstand wurde nicht gefunden."}), 404
