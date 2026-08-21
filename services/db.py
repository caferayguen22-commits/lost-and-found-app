import os

from dotenv import load_dotenv
from pymongo import MongoClient
from openai import OpenAI

# Umweltvariablen laden
load_dotenv()

# Konfiguration via Environment Variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "lost_and_found_db")

# MongoDB Client-Initialisierung
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client[DB_NAME]
    items_collection = db["items"]
    stations_collection = db["berlin_stations"]
except Exception as e:
    print(f"[WARNUNG] MongoDB-Verbindung konnte nicht direkt aufgebaut werden: {e}")

# OpenAI Client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
