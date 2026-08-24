import json
import secrets

from flask import Blueprint, jsonify, request, render_template
from bson.objectid import ObjectId
from openai import OpenAIError

from services.db import items_collection, stations_collection, openai_client
from services.location_service import geocode_berlin_address, haversine_distance_km
from services.prompt_service import build_found_prompt, build_lost_prompt
from services.product_catalog import PRODUCT_DB, COLOR_OPTIONS, CASE_OPTIONS_BY_CATEGORY
from services.email_service import send_match_notification

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
    Deterministische Stationsempfehlung direkt aus MongoDB -- keine KI, keine
    Halluzination. Sind in `origin` (dict mit 'lat'/'lon') Koordinaten
    vorhanden, wird unter den passenden Kandidaten per Haversine-Formel
    (reines Python) die wirklich nächstgelegene Station berechnet:
    1. bevorzugt unter Stationen, die exakt `category` bedienen
    2. sonst unter den allgemeinen "Straße / Sonstiges"-Stationen
       (kategorie-spezifische Stationen wie das BVG-Zentralfundbüro sind
       sonst fälschlich auch für ungeeignete Funde die "nächste" Station)
    Ohne nutzbare Koordinaten greift die bisherige, rein kategoriebasierte
    Auswahl als Fallback.
    """
    if origin and origin.get('lat') is not None and origin.get('lon') is not None:
        with_coords = {"lat": {"$ne": None}, "lon": {"$ne": None}}
        candidates = list(stations_collection.find({"serves_category": category, **with_coords}))
        if not candidates:
            candidates = list(stations_collection.find({"serves_category": GENERAL_STATION_CATEGORY, **with_coords}))

        if candidates:
            nearest = min(
                candidates,
                key=lambda s: haversine_distance_km(origin['lat'], origin['lon'], s['lat'], s['lon'])
            )
            return {
                "name": nearest.get('name'),
                "address": nearest.get('address'),
                "district": nearest.get('district'),
                "distance_km": round(
                    haversine_distance_km(origin['lat'], origin['lon'], nearest['lat'], nearest['lon']), 1
                )
            }

    # Fallback ohne nutzbare Koordinaten: bisherige rein kategoriebasierte Auswahl
    station = stations_collection.find_one({"serves_category": category})
    if not station:
        station = stations_collection.find_one({"name": "Zentrales Fundbüro Berlin"})
    if not station:
        return None
    return {
        "name": station.get('name'),
        "address": station.get('address'),
        "district": station.get('district')
    }


@items_bp.route('/')
def home():
    return render_template('index.html')


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
    data['category'] = category

    title = data.get('title', 'Unbekannter Gegenstand')
    description = data.get('description', 'Keine Beschreibung vorhanden')
    raw_location = data.get('location', 'Kein spezifischer Ort angegeben')
    current_location = data.get('current_location', raw_location)

    location_data = geocode_berlin_address(raw_location)
    if location_data:
        corrected_location = (
            f"{location_data.get('road') or raw_location} "
            f"{location_data.get('house_number') or ''}, "
            f"{location_data.get('postcode') or ''} Berlin "
            f"({location_data.get('district') or 'Bezirk unbekannt'})"
        ).strip()
        data['corrected_location'] = corrected_location
        data['location_details'] = location_data
    else:
        corrected_location = raw_location
        data['corrected_location'] = raw_location
        data['location_details'] = None

    # Ausgangspunkt für die Distanzberechnung zur Abgabestation: bevorzugt der
    # aktuelle Standort (falls angegeben und geocodierbar), sonst der Fundort.
    current_location_input = data.get('current_location')
    if current_location_input:
        distance_origin = geocode_berlin_address(current_location_input) or location_data
    else:
        distance_origin = location_data

    data['tracking_code'] = generate_tracking_code()
    data['match_found'] = False
    data['matched_item_id'] = None
    data['match_probability'] = None

    if item_type == 'found':
        data['user_hint'] = (
            "Danke, dass du ein ehrlicher Finder bist! Hilf dem suchenden Besitzer, "
            "seinen Gegenstand schnell wiederzufinden: Je genauer du Details beschreibst, "
            "desto sicherer schlägt unser automatisches KI-Matching an."
        )
    else:
        data['user_hint'] = (
            "Um die Chancen für ein erfolgreiches Matching zu maximieren, beschreibe "
            "deinen Verlust bitte so präzise wie möglich."
        )

    # --- Bidirektionales Matching: IMMER gegen die jeweils andere Liste prüfen ---
    opposite_type = 'lost' if item_type == 'found' else 'found'
    other_items_cursor = items_collection.find({"type": opposite_type, "category": category})
    other_items_list = [
        {
            "id": str(item['_id']),
            "title": item.get('title'),
            "description": item.get('description'),
            "location": item.get('corrected_location', item.get('location')),
        }
        for item in other_items_cursor
    ]

    parsed_result = {
        "summary": None,
        "match_found": False,
        "matched_item_id": None,
        "match_probability": None,
        "recommended_station": None,
        "matched_doc": None
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

    data['ai_summary'] = parsed_result.get('summary')
    data['recommended_station'] = None
    if item_type == 'found':
        data['recommended_station'] = find_recommended_station(category, origin=distance_origin)

    match_id = parsed_result.get('matched_item_id')
    if parsed_result.get('match_found') and match_id:
        try:
            matched_object_id = ObjectId(match_id)
            matched_doc = items_collection.find_one({"_id": matched_object_id})
        except Exception:
            matched_doc = None

        if matched_doc:
            data['match_found'] = True
            data['matched_item_id'] = match_id
            data['match_probability'] = parsed_result.get('match_probability')

            items_collection.update_one(
                {"_id": matched_object_id},
                {"$set": {
                    "match_found": True,
                    "match_probability": parsed_result.get('match_probability')
                }}
            )

    result = items_collection.insert_one(data)
    new_id = str(result.inserted_id)

    # E-Mail-Benachrichtigungen an beide Seiten, sofern hinterlegt
    if data['match_found']:
        if matched_doc and matched_doc.get('email'):
            send_match_notification(
                to_email=matched_doc['email'],
                item_title=matched_doc.get('title', 'Gegenstand'),
                tracking_code=matched_doc.get('tracking_code'),
                match_probability=data['match_probability']
            )
        if data.get('email'):
            send_match_notification(
                to_email=data['email'],
                item_title=data.get('title', 'Gegenstand'),
                tracking_code=data['tracking_code'],
                match_probability=data['match_probability']
            )

    return jsonify({
        "status": "success",
        "message": "Meldung erfolgreich angelegt.",
        "id": new_id,
        "tracking_code": data['tracking_code'],
        "ai_summary": data['ai_summary'],
        "match_found": data['match_found'],
        "match_probability": data['match_probability'],
        "recommended_station": data['recommended_station'],
        "hint": data['user_hint']
    }), 201


@items_bp.route('/api/items', methods=['GET'])
def get_items():
    items_cursor = items_collection.find()
    all_items = []
    for item in items_cursor:
        item['_id'] = str(item['_id'])
        all_items.append(item)
    return jsonify(all_items), 200


@items_bp.route('/api/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        result = items_collection.delete_one({'_id': ObjectId(item_id)})
        if result.deleted_count == 1:
            return jsonify({"status": "success", "message": "Gegenstand erfolgreich entfernt."}), 200
        return jsonify({"status": "error", "message": "Gegenstand wurde nicht gefunden."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "Ungültige ID übergeben."}), 400


@items_bp.route('/api/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Keine Daten übergeben."}), 400

        result = items_collection.update_one({'_id': ObjectId(item_id)}, {'$set': data})

        if result.matched_count == 1:
            return jsonify({"status": "success", "message": "Gegenstand erfolgreich aktualisiert!"}), 200
        return jsonify({"status": "error", "message": "Gegenstand wurde nicht gefunden."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "Ungültige ID übergeben."}), 400
