import re
from difflib import SequenceMatcher

SIMILARITY_THRESHOLD = 0.8

# Wie viel Anteil des geheimen Merkmals (als zusammenhängender Textblock)
# in der Beschreibung wiedergefunden werden muss, damit die Überlappungs-
# Warnung anschlägt. Bewusst kein 100%-Match nötig -- verzeiht leicht
# andere Formulierung drumherum, verlangt aber einen wesentlichen Kernteil.
OVERLAP_THRESHOLD = 0.6


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


def check_secret_feature_overlap(secret_feature: str, description: str) -> bool:
    """
    Rein deterministische, lokale Prüfung (kein KI-Aufruf -- das geheime
    Merkmal darf niemals an OpenAI gehen, auch nicht zur Prüfung, ob es "zu
    leicht erratbar" ist, siehe lernnotizen.md), ob das geheime Merkmal
    wörtlich oder nahezu wörtlich auch in der öffentlichen Beschreibung
    auftaucht. Fängt den häufigsten Fehler ab (Merkmal aus Versehen doppelt
    eingetragen), erkennt aber KEIN ausgeklügeltes Erraten -- das ist bewusst
    kein vollständiger Schutz, nur eine Warnung an den Finder.

    Anders als compare_secret_feature() (Vergleich zweier etwa gleich langer
    Strings) muss hier ein kurzer Text (secret_feature) innerhalb eines
    typischerweise viel längeren Texts (description) gesucht werden --
    deshalb find_longest_match() statt eines Gesamt-ratio()-Vergleichs.
    """
    secret_norm = _normalize(secret_feature)
    desc_norm = _normalize(description)
    if not secret_norm or not desc_norm:
        return False

    matcher = SequenceMatcher(None, desc_norm, secret_norm)
    match = matcher.find_longest_match(0, len(desc_norm), 0, len(secret_norm))
    overlap_ratio = match.size / len(secret_norm)
    return overlap_ratio >= OVERLAP_THRESHOLD
