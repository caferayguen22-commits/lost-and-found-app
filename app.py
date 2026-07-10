from flask import Flask, jsonify, request
from pymongo import MongoClient

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

# Start des lokalen Entwicklungsservers
if __name__ == '__main__':
    app.run(debug=True, port=5000)