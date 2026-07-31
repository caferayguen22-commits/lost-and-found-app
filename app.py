import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from openai import OpenAI, OpenAIError
from location_service import geocode_berlin_address
from prompt_service import build_found_prompt, build_lost_prompt
from product_catalog import PRODUCT_DB, COLOR_OPTIONS, CASE_OPTIONS_BY_CATEGORY

# Umweltvariablen laden
load_dotenv()

app = Flask(__name__)

# Konfiguration via Environment Variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "lost_and_found_db")

# MongoDB Client-Initialisierung
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client[DB_NAME]
    items_collection = db["items"]
    stations_collection = db["berlin_stations"]
except Exception as e:
    print(f"[WARNUNG] MongoDB-Verbindung konnte nicht direkt aufgebaut werden: {e}")

# OpenAI Client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/product-catalog', methods=['GET'])
def get_product_catalog():
    return jsonify({
        "brands": PRODUCT_DB,
        "colors": COLOR_OPTIONS,
        "cases": CASE_OPTIONS_BY_CATEGORY
    }), 200


@app.route('/api/items', methods=['POST'])
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

    # --- NEU: echte Standortkorrektur statt KI-Raten ---
    location_data = geocode_berlin_address(raw_location)

    if location_data:
        corrected_location = (
            f"{location_data.get('road') or raw_location} "
            f"{location_data.get('house_number') or ''}, "
            f"{location_data.get('postcode') or ''} Berlin "
            f"({location_data.get('district') or 'Berirk unbekannt'})"
        ).strip()
        data['corrected_location'] = corrected_location
        data['location_details'] = location_data  # lat/lot etc. für später (z.B. Stationsdistanz)
    else:
        corrected_location = raw_location
        data['corrected_location'] = raw_location
        data['location_details'] = None


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

    try:
        if item_type == 'found':
            lost_items_cursor = items_collection.find({"type": "lost", "category": category})
            lost_items_list = [
                {
                    "id": str(item['_id']),
                    "category": item.get('category', 'Sonstiges'),
                    "title": item.get('title'),
                    "description": item.get('description'),
                    "location": item.get('location'),
                }
                for item in lost_items_cursor
            ]

            stations_cursor = stations_collection.find()
            stations_list = [
                {
                    "name": station.get('name'),
                    "address": station.get('address'),
                    "district": station.get('district'),
                    "serves_category": station.get('serves_category')
                }
                for station in stations_cursor
            ][:20]

            system_message, prompt = build_found_prompt(
                category=category,
                title=title,
                description=description,
                corrected_location=corrected_location,
                current_location=current_location,
                lost_items_list=lost_items_list,
                stations_list=stations_list
            )
        else:
            system_message, prompt = build_lost_prompt(
                category=category,
                title=title,
                description=description,
                corrected_location=corrected_location
            )

        ai_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            timeout=15.0
        )
        data['ai_report'] = ai_response.choices[0].message.content

    except OpenAIError as oe:
        data['ai_report'] = f"KI-Bericht derzeit nicht verfügbar (OpenAI API Fehler: {str(oe)})."
    except Exception as e:
        data['ai_report'] = f"KI-Bericht konnte nicht generiert werden: {str(e)}"

    result = items_collection.insert_one(data)

    return jsonify({
        "status": "success",
        "message": "Meldung erfolgreich angelegt.",
        "id": str(result.inserted_id),
        "ai_report": data['ai_report'],
        "hint": data['user_hint']
    }), 201


@app.route('/api/items', methods=['GET'])
def get_items():
    items_cursor = items_collection.find()
    all_items = []
    for item in items_cursor:
        item['_id'] = str(item['_id'])
        all_items.append(item)
    return jsonify(all_items), 200


@app.route('/api/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        result = items_collection.delete_one({'_id': ObjectId(item_id)})
        if result.deleted_count == 1:
            return jsonify({"status": "success", "message": "Gegenstand erfolgreich entfernt."}), 200
        return jsonify({"status": "error", "message": "Gegenstand wurde nicht gefunden."}), 404
    except Exception:
        return jsonify({"status": "error", "message": "Ungültige ID übergeben."}), 400


@app.route('/api/items/<item_id>', methods=['PUT'])
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


@app.route('/api/stations', methods=['GET'])
def get_stations():
    try:
        stations = list(stations_collection.find())
        for station in stations:
            station['_id'] = str(station['_id'])
        return jsonify(stations), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fehler beim Abrufen: {str(e)}"}), 500


@app.route('/api/stations/recommend', methods=['GET'])
def recommend_stations():
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({"status": "error", "message": "Kategorie angeben (?category=...)."}), 400

        station = stations_collection.find_one({"serves_category": category})

        if station:
            station['_id'] = str(station['_id'])
            return jsonify({"status": "success", "recommended_station": station}), 200

        backup_station = stations_collection.find_one({"name": "Zentrales Fundbüro Berlin"})
        if backup_station:
            backup_station['_id'] = str(backup_station['_id'])

        return jsonify({
            "status": "success",
            "message": "Keine spezifische Station für diese Kategorie gefunden.",
            "recommended_station": backup_station
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fehler bei der Empfehlung: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5003)