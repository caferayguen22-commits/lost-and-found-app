import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from openai import OpenAI, OpenAIError

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
            ]

            prompt = (
                f"=== NEUER FUNDGEGENSTAND ===\n"
                f"Kategorie: {category}\n"
                f"Gegenstand: {title}\n"
                f"Beschreibung: {description}\n"
                f"Fundort: {raw_location}\n"
                f"Aktueller Standort des Finders: {current_location}\n\n"
                f"=== GEFILTERTE VERLUSTMELDUNGEN (NUR KATEGORIE '{category}') ===\n"
                f"{lost_items_list}\n\n"
                f"=== VERFÜGBARE BERLINER ABGABESTATIONEN ===\n"
                f"{stations_list[:20]}\n\n"
                f"Aufgaben:\n"
                f"1. ORTS-CORRECTOR (BERLIN): Prüfe den Fundort ('{raw_location}') auf Rechtschreibung. "
                f"Schreibe ganz oben als ERSTE ZEILE exakt folgendes Format mit 5-stelliger Postleitzahl:\n"
                f"**KORRIGIERTER ORT:** [Straße + Hausnummer], [5-stellige PLZ] Berlin ([Bezirk])\n\n"
                f"2. ZUSAMMENFASSUNG: Erstelle eine ultrakurze, packende Zusammenfassung. Keine Emojis!\n"
                f"3. MATCHING-ANALYSE: Vergleiche den Fund AUSSCHLIESSLICH mit den gefilterten Verlustmeldungen. "
                f"Nenne bei einem Match die Match-ID und die Wahrscheinlichkeit in %.\n"
                f"4. EMPFEHLUNG & WEGBESCHREIBUNG: Empfiehl eine passende Abgabestation und gib eine kurze, "
                f"praktische Wegbeschreibung ausgehend vom aktuellen Standort ('{current_location}') "
                f"mit konkreten Berliner ÖPNV-Linien (U-Bahn/S-Bahn/Bus)."
            )

            system_message = (
                "Du bist das smarte, dynamische Herzstück unserer Lost & Found Community in Berlin. "
                "Deine Sprache ist modern, klar, absolut nahbar, motivierend und direkt. Verwende KEINE Emojis. "
                "Nutze psychologische Trigger: Gib dem Finder das Gefühl, ein Held auf einer Mission zu sein. "
                "Achte penibel darauf, Orte in Berlin korrekt zu schreiben und den Bezirk hinzuzufügen."
            )
        else:
            prompt = (
                f"=== NEUE VERLUSTMELDUNG ===\n"
                f"Kategorie: {category}\n"
                f"Gegenstand: {title}\n"
                f"Beschreibung: {description}\n"
                f"Eingegebener Verlustort: {raw_location}\n\n"
                f"Aufgabe:\n"
                f"1. Korrigiere eventuelle Rechtschreibfehler beim Ort ('{raw_location}') und füge den Berliner Bezirk hinzu. "
                f"Schreibe ganz oben erste Zeile:\n**KORRIGIERTER ORT:** [Genaue Ortsbezeichnung inkl. Bezirk, Berlin]\n\n"
                f"2. Erstelle eine kurze, empathische und moderne Zusammenfassung für die Verlustmeldung. Keine Emojis."
            )
            system_message = "Erstelle eine kurze, moderne Zusammenfassung einer Verlustmeldung. Keine Emojis."

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