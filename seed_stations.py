import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB Verbindung aufbauen
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client['lost_and_found_db']
stations_collection = db['berlin_stations']

# Alle echten Berliner Hauptanlaufstellen & ALLE 37 Polizeiabschnitte
berlin_stations = [
    # --- ZENTRALE FUNDBÜROS ---
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
        "serves_category": "U-Bahn",
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

    # --- DIREKTION 1 (NORD: Reinickendorf, Pankow, Spandau) ---
    {"name": "Polizeiabschnitt 11", "type": "Polizeidienststelle", "address": "Lietzenburger Str. 30, 10789 Berlin", "district": "Charlottenburg-Wilmersdorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 12", "type": "Polizeidienststelle", "address": "Kaiser-Friedrich-Str. 104, 10585 Berlin", "district": "Charlottenburg-Wilmersdorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 13", "type": "Polizeidienststelle", "address": "Bismarckstr. 111, 10625 Berlin", "district": "Charlottenburg-Wilmersdorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 14", "type": "Polizeidienststelle", "address": "An der Urania 19, 10787 Berlin", "district": "Tempelhof-Schöneberg", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 15", "type": "Polizeidienststelle", "address": "Neuendorfer Str. 90, 13585 Berlin", "district": "Spandau", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 16", "type": "Polizeidienststelle", "address": "Moritzstr. 10, 13597 Berlin", "district": "Spandau", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 17", "type": "Polizeidienststelle", "address": "Oraniendamm 68, 13469 Berlin", "district": "Reinickendorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 18", "type": "Polizeidienststelle", "address": "Antonienstr. 40, 13403 Berlin", "district": "Reinickendorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},

    # --- DIREKTION 2 (WEST: Charlottenburg-Wilmersdorf, Spandau, Steglitz-Zehlendorf) ---
    {"name": "Polizeiabschnitt 21", "type": "Polizeidienststelle", "address": "Moritzstr. 10, 13597 Berlin", "district": "Spandau", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 22", "type": "Polizeidienststelle", "address": "Insterburgallee 2, 14055 Berlin", "district": "Charlottenburg-Wilmersdorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 23", "type": "Polizeidienststelle", "address": "Gothaer Str. 19, 10823 Berlin", "district": "Tempelhof-Schöneberg", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 24", "type": "Polizeidienststelle", "address": "Bürgerstr. 2, 12347 Berlin", "district": "Neukölln", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 25", "type": "Polizeidienststelle", "address": "Eiswaldtstr. 18, 12249 Berlin", "district": "Steglitz-Zehlendorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 26", "type": "Polizeidienststelle", "address": "Sonnentaler Weg 1, 14169 Berlin", "district": "Steglitz-Zehlendorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 27", "type": "Polizeidienststelle", "address": "Martin-Buber-Str. 12, 14163 Berlin", "district": "Steglitz-Zehlendorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 28", "type": "Polizeidienststelle", "address": "Potsdamer Chaussee 63, 14129 Berlin", "district": "Steglitz-Zehlendorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},

    # --- DIREKTION 3 (MITTE: Mitte, Friedrichshain-Kreuzberg) ---
    {"name": "Polizeiabschnitt 31", "type": "Polizeidienststelle", "address": "Brunnenstr. 173, 10115 Berlin", "district": "Mitte", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 32", "type": "Polizeidienststelle", "address": "Keibelstraße 36, 10178 Berlin", "district": "Mitte", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 33", "type": "Polizeidienststelle", "address": "Perleberger Str. 61a, 10559 Berlin", "district": "Mitte", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 34", "type": "Polizeidienststelle", "address": "Pankstr. 29, 13357 Berlin", "district": "Mitte", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 35", "type": "Polizeidienststelle", "address": "Genthiner Str. 38, 10785 Berlin", "district": "Mitte", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 36", "type": "Polizeidienststelle", "address": "Eichenstr. 1, 12435 Berlin", "district": "Treptow-Köpenick", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},

    # --- DIREKTION 4 (SÜD: Tempelhof-Schöneberg, Neukölln) ---
    {"name": "Polizeiabschnitt 41", "type": "Polizeidienststelle", "address": "Storkower Str. 134, 10407 Berlin", "district": "Pankow", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 42", "type": "Polizeidienststelle", "address": "Eberswalder Str. 6, 10437 Berlin", "district": "Pankow", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 43", "type": "Polizeidienststelle", "address": "Dietzgenstr. 42, 13156 Berlin", "district": "Pankow", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 44", "type": "Polizeidienststelle", "address": "Storkower Str. 134, 10407 Berlin", "district": "Pankow", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 45", "type": "Polizeidienststelle", "address": "Rathausstr. 27, 10178 Berlin", "district": "Mitte", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 46", "type": "Polizeidienststelle", "address": "Friesenstr. 16, 10965 Berlin", "district": "Friedrichshain-Kreuzberg", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 47", "type": "Polizeidienststelle", "address": "Krollstr. 10, 12247 Berlin", "district": "Steglitz-Zehlendorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 48", "type": "Polizeidienststelle", "address": "Friedrich-Wilhelm-Str. 82, 12103 Berlin", "district": "Tempelhof-Schöneberg", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},

    # --- DIREKTION 5 (OST: Marzahn-Hellersdorf, Lichtenberg, Treptow-Köpenick) ---
    {"name": "Polizeiabschnitt 51", "type": "Polizeidienststelle", "address": "Friesenstraße 16, 10965 Berlin", "district": "Friedrichshain-Kreuzberg", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 52", "type": "Polizeidienststelle", "address": "Wedekindstr. 10, 10243 Berlin", "district": "Friedrichshain-Kreuzberg", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 53", "type": "Polizeidienststelle", "address": "Sonnenallee 291, 12057 Berlin", "district": "Neukölln", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 54", "type": "Polizeidienststelle", "address": "Rudower Str. 75, 12351 Berlin", "district": "Neukölln", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 55", "type": "Polizeidienststelle", "address": "Pelikanstr. 21, 12355 Berlin", "district": "Neukölln", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 56", "type": "Polizeidienststelle", "address": "Regattastr. 16, 12527 Berlin", "district": "Treptow-Köpenick", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 61", "type": "Polizeidienststelle", "address": "Sonnenallee 291, 12057 Berlin", "district": "Neukölln", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 62", "type": "Polizeidienststelle", "address": "Nöldnerstr. 31, 10317 Berlin", "district": "Lichtenberg", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 63", "type": "Polizeidienststelle", "address": "Seelenbinderstr. 54, 12555 Berlin", "district": "Treptow-Köpenick", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 64", "type": "Polizeidienststelle", "address": "Cecilienstr. 92, 12683 Berlin", "district": "Marzahn-Hellersdorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 65", "type": "Polizeidienststelle", "address": "Märkische Allee 162, 12681 Berlin", "district": "Marzahn-Hellersdorf", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."},
    {"name": "Polizeiabschnitt 66", "type": "Polizeidienststelle", "address": "Prerower Platz 4, 13051 Berlin", "district": "Lichtenberg", "serves_category": "Straße / Sonstiges", "note": "24/7 erreichbar."}
]

def seed_database():
    # Kollektion leeren
    stations_collection.delete_many({})

    # Alle 40 Stationen (37 Polizeidienststellen + 3 Fundbüros) einfügen
    result = stations_collection.insert_many(berlin_stations)
    print(f"✅ Erfolgreich {len(result.inserted_ids)} Anlaufstellen (alle 37 Berliner Polizeiabschnitte + 3 Fundbüros) in MongoDB eingetragen!")

if __name__ == "__main__":
    seed_database()