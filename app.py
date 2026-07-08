from flask import Flask, jsonify
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

# Start des lokalen Entwicklungsservers
if __name__ == '__main__':
    app.run(debug=True, port=5000)