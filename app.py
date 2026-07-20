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


# CRUD: CREATE (Erstellen einer Meldung inklusive KI-Bericht und Matching)
@app.route('/api/items', methods=['POST'])
def create_item():
    """
    Endpunkt zum Erstellen einer neuen Meldung (Fund oder Verlust).
    Validiert den Typ strikt und gleicht Funde mittels KI gegen Verlustmeldungen ab.
    Integriert ein psychologisch optimiertes, motivierendes Belohnungssystem.
    """
    data = request.get_json()

    # Validierung: Überprüfen, ob überhaupt Daten übermittelt wurden
    if not data:
        return jsonify({
            "status": "error",
            "message": "Keine Daten übergeben."
        }), 400

    # Strikte Validierung des Typs (Verhindert Fehlinterpretationen der API)
    item_type = data.get('type')
    if item_type not in ['lost', 'found']:
        return jsonify({
            "status": "error",
            "message": "Ungültiger oder fehlender Typ. Erlaubt sind ausschließlich 'lost' oder 'found'."
        }), 400

    # Extraktion der relevanten Felder für die Verarbeitung
    title = data.get('title', 'Unbekannter Gegenstand')
    description = data.get('description', 'Keine Beschreibung vorhanden')
    location = data.get('location', 'Kein spezifischer Ort angegeben')

    # Psychologisch optimierter Hinweis zur Motivierung des Nutzers
    if item_type == 'found':
        data['user_hint'] = (
            "Danke, dass du ein ehrlicher Finder bist! Hilf dem suchenden Besitzer, "
            "seinen Gegenstand schnell wiederzufinden: Je genauer du Details wie "
            "Hülle (Farbe/Material), Displaykratzer, Risse, Schäden oder das "
            "Sperrbildschirm-Hintergrundbild beschreibst, desto sicherer schlägt unser "
            "automatisches KI-Matching an."
        )
    else:
        data['user_hint'] = (
            "Um die Chancen für ein erfolgreiches Matching zu maximieren, beschreibe "
            "deinen Verlust bitte so präzise wie möglich (z. B. besondere Merkmale, "
            "Kratzer, Hüllen oder Hintergrundbilder)."
        )

    try:
        # Fall 1: Ein Gegenstand wurde gefunden -> Matching-Prozess starten
        if item_type == 'found':
            # Abrufen aller existierenden Verlustmeldungen aus der Datenbank
            lost_items_cursor = items_collection.find({"type": "lost"})
            lost_items_list = []
            for item in lost_items_cursor:
                lost_items_list.append({
                    "id": str(item['_id']),
                    "title": item.get('title'),
                    "description": item.get('description'),
                    "location": item.get('location'),
                })

            # Formulierung des Prompts für Berichterstellung und Matching-Analyse (Gamified & Token-schonend)
            prompt = (
                f"=== NEUER FUNDGEGENSTAND ===\n"
                f"Gegenstand: {title}\n"
                f"Beschreibung: {description}\n"
                f"Fundort: {location}\n\n"
                f"=== EXISTIERENDE VERLUSTMELDUNGEN IN DER DATENBANK ===\n"
                f"{lost_items_list}\n\n"
                f"Aufgaben:\n"
                f"1. Erstelle eine ultrakurze, packende Zusammenfassung des Fundes. Nutze keine Emojis! Mach es modern, energiegeladen und leicht lesbar.\n"
                f"2. Vergleiche den Fund mit den Verlustmeldungen. Wenn ein Match existiert, berechne die Wahrscheinlichkeit in Prozent und feiere den Finder psychologisch als potenziellen Helden, der kurz davor steht, jemandes Tag zu retten! Nenne die Match-ID deutlich und hebe Übereinstimmungen (Farbe, Zustand, Details) prägnant hervor. Falls kein Match existiert, motiviere kurz weiterzusuchen."
            )

            ai_response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Du bist das smarte, dynamische Herzstück unserer Lost & Found Community. "
                            "Deine Sprache ist modern, klar, absolut nahbar, motivierend und direkt. Verwende KEINE Emojis. "
                            "Nutze psychologische Trigger: Gib dem Finder das Gefühl, ein Held auf einer Mission zu sein. "
                            "Vermeide bürokratische Formulierungen wie 'Vorfallsbericht', 'Maßnahmen' oder 'Unterschrift'. "
                            "Arbeite mit kurzen Sätzen, klaren Markdown-Hervorhebungen und maximaler Übersichtlichkeit."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.6
            )
            data['ai_report'] = ai_response.choices[0].message.content

        # Fall 2: Ein Gegenstand wird als verloren gemeldet -> Nur Bericht generieren
        else:
            prompt = (
                f"Erstelle eine moderne, direkt auf den Punkt kommende Zusammenfassung für diese Verlustmeldung.\n"
                f"Gegenstand: {title}\n"
                f"Beschreibung: {description}\n"
                f"Verlustort: {location}"
            )
            ai_response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Erstelle eine kurze, moderne und übersichtliche Zusammenfassung einer Verlustmeldung. "
                            "Nutze KEINE Emojis. Die Sprache soll empathisch, locker, direkt und klar strukturiert sein – absolut kein Behördenstil."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            data['ai_report'] = ai_response.choices[0].message.content

    except Exception as e:
        # Fallback-Verhalten bei API-Fehlern
        data['ai_report'] = f"KI-Bericht konnte nicht generiert werden. Fehler: {str(e)}"

    # Einfügen des validierten und erweiterten Dokuments in die MongoDB
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