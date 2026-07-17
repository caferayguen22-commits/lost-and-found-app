import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB Verbindung aufbauen
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client['lost_and_found_db'] # Die Datenbank
stations_collection = db['berlin_stations'] # Die neue Kollektion

# Testdaten für Berliner Anlaufstellen
berlin_stations = [
    {
        "name": "Zentrales Fundbüro Berlin",
        "type": "Fundbüro",
        "address": "Platz der Luftbrücke 6, 12101 Berlin",
        "district": "Tempelhof-Schöneberg"

    },
    {
        "name": "Polizeiabschnitt 51 (Kreuzberg)",
        "type": "Polizeidienststelle",
        "address": "Friesenstraße 16, 10965 Berlin",
        "district": "Friedrichshain-Kreuzberg"
    },
    {
        "name": "Polizeiabschnitt 32 (Mitte)",
        "type": "Polizeidienststelle",
        "address": "Keibelstraße 36, 10178 Berlin",
        "district": "Mitte"
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