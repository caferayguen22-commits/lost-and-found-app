import os
import sqlite3

from dotenv import load_dotenv
from openai import OpenAI

# Umweltvariablen laden
load_dotenv()

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "lost_and_found.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    address TEXT NOT NULL,
    district TEXT NOT NULL,
    serves_category TEXT NOT NULL,
    note TEXT,
    lat REAL,
    lon REAL
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK (type IN ('lost', 'found')),
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    corrected_location TEXT NOT NULL,
    location_lat REAL,
    location_lon REAL,
    location_postcode TEXT,
    location_district TEXT,
    location_road TEXT,
    location_house_number TEXT,
    current_location TEXT,
    email TEXT,
    image TEXT,
    tracking_code TEXT NOT NULL UNIQUE,
    match_found INTEGER NOT NULL DEFAULT 0,
    matched_item_id INTEGER REFERENCES items(id) ON DELETE SET NULL,
    match_probability INTEGER,
    ai_summary TEXT,
    user_hint TEXT NOT NULL,
    recommended_station_id INTEGER REFERENCES stations(id) ON DELETE SET NULL,
    recommended_station_distance_km REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_connection() -> sqlite3.Connection:
    """Öffnet pro Aufruf eine frische SQLite-Verbindung mit Row-Factory für dict-artigen Zugriff."""
    connection = sqlite3.connect(SQLITE_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    """Legt die Tabellen an, falls sie noch nicht existieren. Idempotent, gefahrlos mehrfach aufrufbar."""
    connection = get_connection()
    try:
        connection.executescript(SCHEMA)
        connection.commit()
    finally:
        connection.close()


# OpenAI Client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
