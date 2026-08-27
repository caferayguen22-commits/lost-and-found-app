from services.db import get_connection
from models.garage_item import GarageItem


def insert_garage_item(item: GarageItem) -> GarageItem:
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO garage_items (user_id, category, title, description, identifying_marks, image, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (item.user_id, item.category, item.title, item.description,
             item.identifying_marks, item.image, item.status)
        )
        connection.commit()
        new_id = cursor.lastrowid
        row = connection.execute("SELECT * FROM garage_items WHERE id = ?", (new_id,)).fetchone()
        return GarageItem.from_row(row)
    finally:
        connection.close()


def get_garage_items_by_user(user_id: int) -> list[GarageItem]:
    """Einzige Leseabfrage für Garage-Inhalte -- filtert IMMER auf SQL-Ebene
    nach user_id, nie erst nachträglich in Python. Es gibt bewusst keine
    ungefilterte 'get_by_id'-Funktion in diesem Modul, damit eine Route
    strukturell gar nicht erst versehentlich fremde Einträge laden kann."""
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM garage_items WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        return [GarageItem.from_row(row) for row in rows]
    finally:
        connection.close()


def update_status(item_id: int, user_id: int, new_status: str) -> bool:
    """user_id ist Teil der WHERE-Klausel, nicht nur eine nachträgliche Prüfung --
    ein User kann so strukturell nie den Status eines fremden Items ändern."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            "UPDATE garage_items SET status = ?, status_changed_at = datetime('now') WHERE id = ? AND user_id = ?",
            (new_status, item_id, user_id)
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_garage_item(item_id: int, user_id: int) -> bool:
    """Ebenfalls user_id direkt in der WHERE-Klausel -- kein Löschen fremder Items möglich."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            "DELETE FROM garage_items WHERE id = ? AND user_id = ?",
            (item_id, user_id)
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def record_check_attempt(ip_address: str) -> None:
    connection = get_connection()
    try:
        connection.execute("INSERT INTO garage_check_attempts (ip_address) VALUES (?)", (ip_address,))
        connection.commit()
    finally:
        connection.close()


def count_recent_check_attempts(ip_address: str, minutes: int) -> int:
    """Rate-Limiting-Basis für die öffentliche Prüf-Funktion. Erster, einfacher
    Wurf: IP-basiert statt pro-Item wie beim geheimen Merkmal, da es hier keinen
    einzelnen 'Ressourcen-Schlüssel' gibt (jemand könnte viele verschiedene
    Seriennummern durchprobieren) -- schwächer als das Item-basierte Limit,
    aber besser als nichts."""
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count FROM garage_check_attempts
            WHERE ip_address = ? AND attempted_at >= datetime('now', ?)
            """,
            (ip_address, f"-{minutes} minutes")
        ).fetchone()
        return row["count"]
    finally:
        connection.close()


def find_by_identifying_marks(marks: str) -> list[GarageItem]:
    """Für die öffentliche Prüf-Funktion (kein Login nötig). Exakter,
    normalisierter Vergleich (Groß-/Kleinschreibung und Leerzeichen egal,
    sonst exakt) -- Seriennummern sind präzise Codes, kein Fließtext wie
    beim geheimen Merkmal, daher bewusst kein unscharfer difflib-Vergleich."""
    normalized = marks.strip().upper()
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM garage_items WHERE UPPER(TRIM(identifying_marks)) = ?",
            (normalized,)
        ).fetchall()
        return [GarageItem.from_row(row) for row in rows]
    finally:
        connection.close()
