from services.db import get_connection
from models.claim_attempt import ClaimAttempt


def record_attempt(attempt: ClaimAttempt) -> ClaimAttempt:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO claim_attempts (item_id, claimant_email, success) VALUES (?, ?, ?)",
            (attempt.item_id, attempt.claimant_email, int(attempt.success))
        )
        connection.commit()
        new_id = cursor.lastrowid
        row = connection.execute("SELECT * FROM claim_attempts WHERE id = ?", (new_id,)).fetchone()
        return ClaimAttempt.from_row(row)
    finally:
        connection.close()


def count_recent_attempts(item_id: int, minutes: int) -> int:
    """Anzahl Versuche für dieses Item innerhalb der letzten `minutes` Minuten -- Basis fürs Rate-Limiting."""
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count FROM claim_attempts
            WHERE item_id = ? AND attempted_at >= datetime('now', ?)
            """,
            (item_id, f"-{minutes} minutes")
        ).fetchone()
        return row["count"]
    finally:
        connection.close()


def has_verified_claim(item_id: int) -> bool:
    """True, wenn für dieses Item schon irgendwann ein erfolgreicher Verifizierungsversuch protokolliert wurde."""
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT 1 FROM claim_attempts WHERE item_id = ? AND success = 1 LIMIT 1",
            (item_id,)
        ).fetchone()
        return row is not None
    finally:
        connection.close()
