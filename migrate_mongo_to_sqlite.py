import os

from pymongo import MongoClient
from dotenv import load_dotenv

from services.db import init_db
from services.stations_repository import insert_station
from models.station import Station

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "lost_and_found_db")


def migrate_stations():
    """
    Übernimmt die bestehenden berlin_stations-Dokumente aus MongoDB 1:1 in die
    neue SQLite-Tabelle -- inkl. bereits vorhandener lat/lon, kein erneutes
    Geocoding nötig. Die items-Collection ist bereits geleert und muss nicht
    migriert werden.
    """
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    mongo_stations = list(db["berlin_stations"].find())

    migrated = 0
    for doc in mongo_stations:
        station = Station(
            name=doc.get("name"),
            type=doc.get("type"),
            address=doc.get("address"),
            district=doc.get("district"),
            serves_category=doc.get("serves_category"),
            note=doc.get("note"),
            lat=doc.get("lat"),
            lon=doc.get("lon")
        )
        insert_station(station)
        migrated += 1

    print(f"✅ {migrated} von {len(mongo_stations)} Stationen aus MongoDB nach SQLite übernommen.")


if __name__ == "__main__":
    init_db()
    migrate_stations()
