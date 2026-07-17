from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson.objectid import ObjectId

# Initialisierung der Flask-Applikation
app = Flask(__name__)

# Konfiguration der MongoDB-Verbindung
# Verbindungsaufbau zur lokalen MongoDB-Instanz über den Standard-Port 27017
client = MongoClient("mongodb://localhost:27017/")

# Definition von Datenbank und Collection für das Projekt
db = client["lost_and_found_db"]
items_collection = db["items"]

# Test-Route zur Überprüfung, ob der Server läuft
@app.route('/')
def home():
    """
    Basis-Endpunkt zur Überprüfung des API- und Datenbank-Status.
    """
    return jsonify({
        "status": "erfolgreich",
        "nachricht": "Willkommen bei der Community Lost & Found App!"
    })

# CRUD: CREATE (Erstellen einer Fundmeldung)
@app.route('/api/items', methods=['POST'])
def create_item():
    """
    Endpunkt zum Erstellen einer neuen Fundmeldung in der Datenbank.
    """
    # Empfangen der JSON-Daten vom Client
    data = request.get_json()

    # Validierung: Überprüfen, ob Daten übermittelt wurden
    if not data:
        return jsonify({
            "status": "error",
            "message": "Keine Daten übergeben"
        }), 400

    # Einfügen des Dokuments in die MongoDB-Collection
    result = items_collection.insert_one(data)

    # Rückmeldung an den Client mit der generierten MongoDB_ID
    return jsonify({
        "status": "success",
        "message": "Fundmeldung erfolgreich angelegt",
        "id": str(result.inserted_id)
    }), 201

@app.route('/api/items', methods=['GET'])
def get_items():
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

        # Prüfen. ob ein Dokument mit dieser ID gefunden wurde
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
    try:
        # Alle Stationen aus der neuen Kollektion abrufen
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

# Start des lokalen Entwicklungsservers
if __name__ == '__main__':
    app.run(debug=True, port=5003)