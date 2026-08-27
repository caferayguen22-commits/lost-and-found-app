from werkzeug.security import generate_password_hash, check_password_hash

MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def is_valid_email(email: str) -> bool:
    """Bewusst simpel -- kein RFC5322-Regex, nur ein Mindest-Sanity-Check."""
    return bool(email) and "@" in email and len(email) <= 254


def is_valid_password(password: str) -> bool:
    """Mindestlänge statt Komplexitätsregeln (Sonderzeichen-Zwang etc.) --
    moderne Empfehlungen wie NIST 800-63B raten von Komplexitätsregeln ab,
    Länge ist der wichtigere Faktor."""
    return bool(password) and len(password) >= MIN_PASSWORD_LENGTH
