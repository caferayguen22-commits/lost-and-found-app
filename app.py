import os
from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient
from bson.objectid import ObjectId

# Laden der Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Initialisierung des OpenAI-Clients
openai_client = OpenAI()

# Initialisierung der Flask-Applikation
app = Flask(__name__)

# Konfiguration der MongoDB-Verbindung
client = MongoClient("mongodb://localhost:27017/")

# Definition von Datenbank und Collection für das Projekt
db = client["lost_and_found_db"]
items_collection = db["items"]


@app.route('/')
def home():
    """
    Basis-Endpunkt, der das visuelle Hauptmenü (Startbildschirm) ausliefert.
    """
    return render_template('index.html')


# CRUD: CREATE (Erstellen einer Meldung inklusive KI-Bericht, Ort-Korrektur & Matching)
@app.route('/api/items', methods=['POST'])
def create_item():
    """
    Endpunkt zum Erstellen einer neuen Meldung (Fund oder Verlust).
    Validiert den Typ strikt, korrigiert Tippfehler bei Berliner Ortsangaben (inkl. Bezirk),
    gleicht Funde mittels KI gegen Verlustmeldungen ab und gibt Empfehlungen für Abgabestationen.
    """
    data = request.get_json()

    # Validierung: Überprüfen, ob überhaupt Daten übermittelt wurden
    if not data:
        return jsonify({
            "status": "error",
            "message": "Keine Daten übergeben."
        }), 400

    # Strikte Validierung des Typs
    item_type = data.get('type')
    if item_type not in ['lost', 'found']:
        return jsonify({
            "status": "error",
            "message": "Ungültiger oder fehlender Typ. Erlaubt sind ausschließlich 'lost' oder 'found'."
        }), 400

    # Extraktion der relevanten Felder
    category = data.get('category', 'Sonstiges')
    title = data.get('title', 'Unbekannter Gegenstand')
    description = data.get('description', 'Keine Beschreibung vorhanden')
    raw_location = data.get('location', 'Kein spezifischer Ort angegeben')

    # Psychologisch optimierter Hinweis zur Motivierung des Nutzers
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
            # Abrufen aller existierenden Verlustmeldungen aus der Datenbank
            lost_items_cursor = items_collection.find({"type": "lost"})
            lost_items_list = []
            for item in lost_items_cursor:
                lost_items_list.append({
                    "id": str(item['_id']),
                    "category": item.get('category', 'Sonstiges'),
                    "title": item.get('title'),
                    "description": item.get('description'),
                    "location": item.get('location'),
                })

            # Abrufen aller registrierten Berliner Abgabestationen/Polizeiabschnitte
            stations_cursor = db['berlin_stations'].find()
            stations_list = []
            for station in stations_cursor:
                stations_list.append({
                    "name": station.get('name'),
                    "address": station.get('address'),
                    "district": station.get('district'),
                    "serves_category": station.get('serves_category')
                })

            # Prompt mit Ort-Korrektur, Matching und Abgabestationen
            prompt = (
                f"=== NEUER FUNDGEGENSTAND ===\n"
                f"Kategorie: {category}\n"
                f"Gegenstand: {title}\n"
                f"Beschreibung: {description}\n"
                f"Eingegebener Ort vom Nutzer: {raw_location}\n\n"
                f"=== EXISTIERENDE VERLUSTMELDUNGEN IN DER DATENBANK ===\n"
                f"{lost_items_list}\n\n"
                f"=== VERFÜGBARE BERLINER ABGABESTATIONEN / POLIZEIABSCHNITTE ===\n"
                f"{stations_list[:20]}\n\n"
                f"Aufgaben:\n"
                f"1. ORTS-CORRECTION (BERLIN): Korrigiere eventuelle Rechtschreibfehler im eingegebenen Ort ('{raw_location}') "
                f"und ordne ihn eindeutig dem passenden Berliner Bezirk / Stadtteil zu (z.B. aus 'hermanplatz' wird 'U Hermannplatz (Neukölln)'). "
                f"Schreibe ganz oben als erste Zeile genau dieses Format:\n"
                f"**KORRIGIERTER ORT:** [Genaue Ortsbezeichnung inkl. Bezirk, Berlin]\n\n"
                f"2. ZUSAMMENFASSUNG: Erstelle eine ultrakurze, packende Zusammenfassung des Fundes. Keine Emojis!\n"
                f"3. MATCHING-ANALYSE: Vergleiche den Fund mit den Verlustmeldungen. Bei einem Match feiere den Finder psychologisch als Helden! Nenne die Match-ID und Wahrscheinlichkeit in %.\n"
                f"4. EMPFEHLUNG ZUR ABGABE: Gib dem Finder basierend auf Ort und Kategorie ({category}) eine konkrete Empfehlung aus der Stationen-Liste, wo er den Gegenstand in Berlin (z. B. Polizeiabschnitt, BVG/S-Bahn Fundbüro) am besten abgeben kann."
            )

            ai_response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Du bist das smarte, dynamische Herzstück unserer Lost & Found Community in Berlin. "
                            "Deine Sprache ist modern, klar, absolut nahbar, motivierend und direkt. Verwende KEINE Emojis. "
                            "Nutze psychologische Trigger: Gib dem Finder das Gefühl, ein Held auf einer Mission zu sein. "
                            "Achte penibel darauf, Orte in Berlin korrekt zu schreiben und den Bezirk hinzuzufügen."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            data['ai_report'] = ai_response.choices[0].message.content

        else:
            # Verlustmeldung: Auch hier lassen wir den Ort prüfen/korrigieren
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
            ai_response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Erstelle eine kurze, moderne Zusammenfassung einer Verlustmeldung. Keine Emojis."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            data['ai_report'] = ai_response.choices[0].message.content

    except Exception as e:
        data['ai_report'] = f"KI-Bericht konnte nicht generiert werden. Fehler: {str(e)}"

    # Einfügen des Dokuments in die MongoDB
    result = items_collection.insert_one(data)

    # Rückmeldung an den Client
    return jsonify({
        "status": "success",
        "message": "Meldung erfolgreich angelegt.",
        "id": str(result.inserted_id),
        "ai_report": data['ai_report'],
        "hint": data['user_hint']
    }), 201


@app.route('/api/items', methods=['GET'])
def get_items():
    """
    Endpunkt zum Abrufen aller Fund- und Verlustmeldungen aus der Datenbank.
    """
    items_cursor = items_collection.find()
    all_items = []
    for item in items_cursor:
        item['_id'] = str(item['_id'])
        all_items.append(item)
    return jsonify(all_items), 200


@app.route('/api/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    """
    Endpunkt zum Löschen einer Meldung anhand ihrer eindeutigen ID.
    """
    try:
        result = items_collection.delete_one({'_id': ObjectId(item_id)})
        if result.deleted_count == 1:
            return jsonify({
                "status": "success",
                "message": "Gegenstand erfolgreich aus dem System entfernt."
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Gegenstand wurde nicht gefunden."
            }), 404
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Ungültige ID übergeben."
        }), 400


@app.route('/api/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    """
    Endpunkt zur Aktualisierung bestehender Felder einer Meldung.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Keine Daten für die Aktualisierung übergeben."
            }), 400

        result = items_collection.update_one(
            {'_id': ObjectId(item_id)},
            {'$set': data}
        )

        if result.matched_count == 1:
            return jsonify({
                "status": "success",
                "message": "Gegenstand erfolgreich aktualisiert!"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Gegenstand wurde nicht gefunden."
            }), 404
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Ungültige ID übergeben."
        }), 400


@app.route('/api/stations', methods=['GET'])
def get_stations():
    """
    Endpunkt zum Abrufen aller registrierten Berliner Abgabestationen.
    """
    try:
        stations = list(db['berlin_stations'].find())
        for station in stations:
            station['_id'] = str(station['_id'])
        return jsonify(stations), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Fehler beim Abrufen der Stationen."
        }), 500


@app.route('/api/stations/recommend', methods=['GET'])
def recommend_stations():
    """
    Endpunkt zur dynamischen Empfehlung einer Abgabestation basierend auf der Fundkategorie.
    """
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({
                "status": "error",
                "message": "Bitte gib eine Kategorie an (z.B. ?category=U-Bahn)."
            }), 400

        station = db['berlin_stations'].find_one({"serves_category": category})

        if station:
            station['_id'] = str(station['_id'])
            return jsonify({
                "status": "success",
                "recommended_station": station
            }), 200
        else:
            backup_station = db['berlin_stations'].find_one({"name": "Zentrales Fundbüro Berlin"})
            if backup_station:
                backup_station['_id'] = str(backup_station['_id'])

            return jsonify({
                "status": "success",
                "message": "Keine spezifische Station für diese Kategorie gefunden. Allgemeine Empfehlung gesendet.",
                "recommended_station": backup_station
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Fehler bei der Empfehlung: {str(e)}"
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5003)