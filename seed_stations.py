import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB Verbindung aufbauen
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client['lost_and_found_db'] # Die Datenbank
stations_collection = db['berlin_stations'] # Die neue Kollektion

# Die echten Berliner Hauptanlaufstellen
berlin_stations = [
    {
        "name": "Zentrales Fundbüro Berlin",
        "type": "Fundbüro",
        "address": "Platz der Luftbrücke 6, 12101 Berlin",
        "district": "Tempelhof-Schöneberg",
        "serves_category": "Straße / Sonstiges",
        "note": "Zuständig für alle Funde auf öffentlichen Straßen, Plätzen oder in Ämtern."

    },
    {
        "name": "BVG-Zentralfundbüro",
        "type": "Fundbüro",
        "address": "Rudolfstraße 1-8, 10245 Berlin",
        "district": "Friedrichshain-Kreuzberg",
        "serves_category": "U-Bahn",  # Deckt auch Bus und Tram ab
        "note": "Zuständig für alle Funde in U-Bahnen, BVG-Bussen und Trams sowie auf deren Bahnhöfen."
    },
    {
"name": "S-Bahn & Deutsche Bahn Fundstelle (Bhf. Lichtenberg)",
        "type": "Fundbüro",
        "address": "Weitlingstraße 22, 10317 Berlin",
        "district": "Lichtenberg",
        "serves_category": "S-Bahn",
        "note": "Zuständig für alle Funde in der S-Bahn, in Regional- und Fernzügen sowie auf Bahnhöfen der Deutschen Bahn."
    },
    {
        "name": "Polizeiabschnitt 51 (Kreuzberg)",
        "type": "Polizeidienststelle",
        "address": "Friesenstraße 16, 10965 Berlin",
        "district": "Friedrichshain-Kreuzberg",
        "serves_category": "Straße / Sonstiges",
        "note": "Kann rund um die Uhr für Abgaben im Bezirk Kreuzberg genutzt werden."
    },
    {
        "name": "Polizeiabschnitt 32 (Mitte)",
        "type": "Polizeidienststelle",
        "address": "Keibelstraße 36, 10178 Berlin",
        "district": "Mitte",
        "serves_category": "Straße / Sonstiges",
        "note": "Kann rund um die Uhr für Abgaben im Bezirk Mitte genutzt werden."
    }
]

def seed_database():
    # kollektion leeren, um Duplikate beim Testen zu vermeiden
    stations_collection.delete_many({})

    # Daten einfügen
    result = stations_collection.insert_many(berlin_stations)
    print(f"Erfolgreich {len(result.inserted_ids)} Stationen in die MongoDB eingetragen!")

if __name__ == "__main__":
    seed_database()