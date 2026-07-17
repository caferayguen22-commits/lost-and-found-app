import os
from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson.objectid import ObjectId

# Laden der Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Initialisierung des OpenAI-Clients
openai_client = OpenAI()

# Initialisierung der Flask-Applikation
app = Flask(__name__)

# Konfiguration der MongoDB-Verbindung
# Verbindungsaufbau zur lokalen MongoDB-Instanz über den Standard-Port 27017
client = MongoClient("mongodb://localhost:27017/")

# Definition von Datenbank und Collection für das Projekt
db = client["lost_and_found_db"]
items_collection = db["items"]


@app.route('/')
def home():
    """
    Basis-Endpunkt zur Überprüfung des API- und Datenbank-Status.
    """
    return jsonify({
        "status": "erfolgreich",
        "nachricht": "Willkommen bei der Community Lost & Found App!"
    })


# CRUD: CREATE (Erstellen einer Fundmeldung inklusive KI-Bericht)
@app.route('/api/items', methods=['POST'])
def create_item():
    """
    Endpunkt zum Erstellen einer neuen Fundmeldung in der Datenbank.
    Integriert eine automatische Generierung eines offiziellen Berichts via OpenAI.
    """
    # Empfangen der JSON-Daten vom Client
    data = request.get_json()

    # Validierung: Überprüfen, ob Daten übermittelt wurden
    if not data:
        return jsonify({
            "status": "error",
            "message": "Keine Daten übergeben"
        }), 400

    # Extraktion der relevanten Felder für die KI-Verarbeitung
    title = data.get('title', 'Unbekannter Gegenstand')
    description = data.get('description', 'Keine Beschreibung vorhanden')
    location = data.get('location', 'Kein spezifischer Fundort angegeben')

    try:
        # Erstellung des Prompts für die Generierung des offiziellen Berichts
        prompt = (
            f"Generiere einen kurzen, professionellen offiziellen Bericht für eine Fundmeldung.\n"
            f"Gegenstand: {title}\n"
            f"Beschreibung: {description}\n"
            f"Fundort: {location}"
        )

        # Anfrage an die OpenAI-API zur Erstellung der Zusammenfassung
        ai_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein präziser und professioneller Assistent für ein digitales Fundbüro. Erstelle kurze, sachliche und strukturiert formatierte Berichte für Fundmeldungen."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5
        )

        # Extrahieren des generierten Textes aus der API-Antwort
        generated_report = ai_response.choices[0].message.content

        # Anhängen des KI-Berichts an das bestehende Datenobjekt vor dem DB-Insert
        data['ai_report'] = generated_report

    except Exception as e:
        # Fallback-Verhalten: Falls die API fehlschlägt, wird der Fehler protokolliert,
        # die Fundmeldung wird jedoch ohne KI-Bericht gespeichert, um die App-Funktion nicht zu blockieren.
        data['ai_report'] = f"KI-Bericht konnte nicht generiert werden. Fehler: {str(e)}"

    # Einfügen des erweiterten Dokuments in die MongoDB-Collection
    result = items_collection.insert_one(data)

    # Rückmeldung an den Client mit der generierten MongoDB_ID und dem KI-Bericht
    return jsonify({
        "status": "success",
        "message": "Fundmeldung inklusive KI-Bericht erfolgreich angelegt",
        "id": str(result.inserted_id),
        "ai_report": data['ai_report']
    }), 201


@app.route('/api/items', methods=['GET'])
def get_items():
    """
    Endpunkt zum Abrufen aller Fundmeldungen aus der Datenbank.
    """
    # Alle Dokumente aus der MongoDB-Collection abrufen
    items_cursor = items_collection.find()

    # Die Daten in eine normale Python-Liste umwandeln
    all_items = []
    for item in items_cursor:
        # Die MongoDB-ID (_id) müssen wir für JSON in einen String umwandeln
        item['_id'] = str(item['_id'])
        all_items.append(item)

    return jsonify(all_items), 200


@app.route('/api/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    """
    Endpunkt zum Löschen einer Fundmeldung anhand ihrer eindeutigen ID.
    """
    try:
        # Dokument anhand der ID aus der MongoDB löschen
        result = items_collection.delete_one({'_id': ObjectId(item_id)})

        if result.deleted_count == 1:
            return jsonify({
                "status": "success",
                "message": "Gegenstand erfolgreich an den Besitzer übergeben und gelöscht!"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Gegenstand wurde nicht gefunden"
            }), 404

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Gegenstand wurde nicht gefunden"
        }), 400


@app.route('/api/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    """
    Endpunkt zur Aktualisierung bestehender Felder einer Fundmeldung.
    """
    try:
        # Die neuen Daten aus dem JSON-Body der Anfrage holen
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "Keine Daten für die Aktualisierung übergeben."
            }), 400

        # Dokument in der MongoDB aktualisieren ($set überschreibt nur die übergebenen Felder)
        result = items_collection.update_one(
            {'_id': ObjectId(item_id)},
            {'$set': data}
        )

        # Prüfen, ob ein Dokument mit dieser ID gefunden wurde
        if result.matched_count == 1:
            return jsonify({
                "status": "success",
                "message": "Gegenstand erfolgreich aktualisiert!"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Gegenstand wurde nicht gefunden"
            }), 404

    except Exception as e:
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
        # Alle Stationen aus der Kollektion abrufen
        stations = list(db['berlin_stations'].find())

        # MongoDB ObjectIds in Strings umwandeln für JSON
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
        # Abrufen der Kategorie aus den Query-Parametern der URL (z.B. ?category=U-Bahn)
        category = request.args.get('category')

        if not category:
            return jsonify({
                "status": "error",
                "message": "Bitte gib eine Kategorie an (z.B. ?category=U-Bahn)."
            }), 400

        # Datenbankabfrage nach einer Station, die diese Kategorie bedient
        station = db['berlin_stations'].find_one({"serves_category": category})

        if station:
            station['_id'] = str(station['_id'])  # ObjectID für JSON umwandeln
            return jsonify({
                "status": "success",
                "recommended_station": station
            }), 200
        else:
            # Fallback: Rückfalloption auf das Zentralfundbüro Berlin, falls keine spezifische Kategorie matcht
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


# Start des lokalen Entwicklungsservers
if __name__ == '__main__':
    app.run(debug=True, port=5003)