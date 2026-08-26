import re
from difflib import SequenceMatcher

SIMILARITY_THRESHOLD = 0.8


def _normalize(text: str) -> str:
    """lowercase, Satzzeichen raus, mehrfache Leerzeichen zusammenfassen."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compare_secret_feature(guess: str, actual: str) -> bool:
    """
    Toleranter Ähnlichkeitsvergleich statt exaktem String-Vergleich -- verzeiht
    Tippfehler und andere Formulierung, verlangt aber weiterhin, dass der
    wesentliche Inhalt getroffen wird (reines Python, difflib aus der
    Standardbibliothek).
    """
    if not guess or not actual:
        return False

    ratio = SequenceMatcher(None, _normalize(guess), _normalize(actual)).ratio()
    return ratio >= SIMILARITY_THRESHOLD
