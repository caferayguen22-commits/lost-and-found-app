from services.db import get_connection


def record_attempt(ip_address: str) -> None:
    connection = get_connection()
    try:
        connection.execute("INSERT INTO photo_analysis_attempts (ip_address) VALUES (?)", (ip_address,))
        connection.commit()
    finally:
        connection.close()


def count_recent_attempts(ip_address: str, minutes: int) -> int:
    """Rate-Limiting-Basis für die Foto-Analyse -- IP-basiert, analog zu
    garage_items_repository.count_recent_check_attempts. Notwendig, weil der
    Endpoint ohne Login erreichbar sein muss (Verlust-/Fund-Formular
    brauchen kein Konto) und jeder Aufruf echtes Geld kostet (Vision-Modell)."""
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count FROM photo_analysis_attempts
            WHERE ip_address = ? AND attempted_at >= datetime('now', ?)
            """,
            (ip_address, f"-{minutes} minutes")
        ).fetchone()
        return row["count"]
    finally:
        connection.close()
