from services.db import get_connection
from models.station import Station


def insert_station(station: Station) -> Station:
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO stations (name, type, address, district, serves_category, note, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                station.name, station.type, station.address, station.district,
                station.serves_category, station.note, station.lat, station.lon
            )
        )
        connection.commit()
        station.id = cursor.lastrowid
        return station
    finally:
        connection.close()


def get_station_by_id(station_id: int) -> Station | None:
    connection = get_connection()
    try:
        row = connection.execute("SELECT * FROM stations WHERE id = ?", (station_id,)).fetchone()
        return Station.from_row(row) if row else None
    finally:
        connection.close()


def get_station_by_name(name: str) -> Station | None:
    connection = get_connection()
    try:
        row = connection.execute("SELECT * FROM stations WHERE name = ?", (name,)).fetchone()
        return Station.from_row(row) if row else None
    finally:
        connection.close()


def get_all_stations() -> list[Station]:
    connection = get_connection()
    try:
        rows = connection.execute("SELECT * FROM stations").fetchall()
        return [Station.from_row(row) for row in rows]
    finally:
        connection.close()


def get_stations_by_category(category: str, only_with_coords: bool = False) -> list[Station]:
    connection = get_connection()
    try:
        query = "SELECT * FROM stations WHERE serves_category = ?"
        if only_with_coords:
            query += " AND lat IS NOT NULL AND lon IS NOT NULL"
        rows = connection.execute(query, (category,)).fetchall()
        return [Station.from_row(row) for row in rows]
    finally:
        connection.close()


def delete_all_stations() -> None:
    """Für erneutes Seeden: leert die Tabelle komplett (z.B. tools/seed_stations.py)."""
    connection = get_connection()
    try:
        connection.execute("DELETE FROM stations")
        connection.commit()
    finally:
        connection.close()
