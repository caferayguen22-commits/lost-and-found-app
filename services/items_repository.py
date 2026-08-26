import dataclasses

from services.db import get_connection
from models.item import Item

_ITEM_COLUMNS = {f.name for f in dataclasses.fields(Item)} - {"id", "created_at"}


def insert_item(item: Item) -> Item:
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO items (
                type, category, title, description, location, corrected_location,
                location_lat, location_lon, location_postcode, location_district,
                location_road, location_house_number, current_location, email, image,
                tracking_code, match_found, matched_item_id, match_probability,
                ai_summary, user_hint, recommended_station_id, recommended_station_distance_km,
                secret_feature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.type, item.category, item.title, item.description, item.location, item.corrected_location,
                item.location_lat, item.location_lon, item.location_postcode, item.location_district,
                item.location_road, item.location_house_number, item.current_location, item.email, item.image,
                item.tracking_code, int(item.match_found), item.matched_item_id, item.match_probability,
                item.ai_summary, item.user_hint, item.recommended_station_id, item.recommended_station_distance_km,
                item.secret_feature
            )
        )
        connection.commit()
        new_id = cursor.lastrowid
    finally:
        connection.close()
    return get_item_by_id(new_id)


def get_item_by_id(item_id: int) -> Item | None:
    connection = get_connection()
    try:
        row = connection.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return Item.from_row(row) if row else None
    finally:
        connection.close()


def get_item_by_tracking_code(tracking_code: str) -> Item | None:
    connection = get_connection()
    try:
        row = connection.execute("SELECT * FROM items WHERE tracking_code = ?", (tracking_code,)).fetchone()
        return Item.from_row(row) if row else None
    finally:
        connection.close()


def get_all_items() -> list[Item]:
    connection = get_connection()
    try:
        rows = connection.execute("SELECT * FROM items").fetchall()
        return [Item.from_row(row) for row in rows]
    finally:
        connection.close()


def get_items_by_type_and_category(item_type: str, category: str) -> list[Item]:
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM items WHERE type = ? AND category = ?", (item_type, category)
        ).fetchall()
        return [Item.from_row(row) for row in rows]
    finally:
        connection.close()


def update_item(item_id: int, **fields) -> bool:
    """Aktualisiert nur Felder, deren Name einer echten Item-Spalte entspricht
    (Allowlist aus den Dataclass-Feldern -- verhindert SQL-Injection über Spaltennamen,
    die anders als Werte nicht parametrisiert werden können)."""
    valid_fields = {k: v for k, v in fields.items() if k in _ITEM_COLUMNS}
    if not valid_fields:
        return False
    if "match_found" in valid_fields:
        valid_fields["match_found"] = int(valid_fields["match_found"])

    set_clause = ", ".join(f"{column} = ?" for column in valid_fields)
    connection = get_connection()
    try:
        cursor = connection.execute(
            f"UPDATE items SET {set_clause} WHERE id = ?",
            (*valid_fields.values(), item_id)
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_item(item_id: int) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute("DELETE FROM items WHERE id = ?", (item_id,))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def mark_matched(item_id: int, probability) -> None:
    """Setzt match_found/match_probability auf dem GEFUNDENEN Match-Partner
    (keine Rückreferenz auf matched_item_id -- entspricht dem bisherigen Verhalten)."""
    connection = get_connection()
    try:
        connection.execute(
            "UPDATE items SET match_found = 1, match_probability = ? WHERE id = ?",
            (probability, item_id)
        )
        connection.commit()
    finally:
        connection.close()
