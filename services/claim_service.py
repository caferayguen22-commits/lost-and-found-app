import re
from difflib import SequenceMatcher

# Kalibriert an einer Reihe realistischer Testfälle (siehe lernnotizen.md):
# umgestellte Wortreihenfolge, weggelassene Füllwörter/Größenangaben und
# deutsche Komposita liegen alle klar über 0.75; falsche/geratene Merkmale
# klar unter 0.42. 0.7 liegt sicher dazwischen, mit Abstand nach beiden Seiten.
SIMILARITY_THRESHOLD = 0.7

# Wie viel Anteil des geheimen Merkmals (als zusammenhängender Textblock)
# in der Beschreibung wiedergefunden werden muss, damit die Überlappungs-
# Warnung anschlägt. Bewusst kein 100%-Match nötig -- verzeiht leicht
# andere Formulierung drumherum, verlangt aber einen wesentlichen Kernteil.
OVERLAP_THRESHOLD = 0.6

# Nur echte Funktionswörter (Artikel, Präpositionen, Hilfsverben, Pronomen) --
# bewusst KEINE Adjektive wie "klein"/"groß", die selbst Teil des gemeinten
# Merkmals sein könnten und den Vergleich sonst künstlich verwässern würden.
_STOPWORDS = {
    "ein", "eine", "einer", "eines", "einem", "einen",
    "der", "die", "das", "des", "dem", "den",
    "und", "oder", "ist", "sind", "war", "hat", "hatte", "habe",
    "von", "mit", "auf", "im", "in", "zu", "am", "an",
    "da", "dort", "es", "gibt", "sich", "noch", "auch", "nur",
}


def _normalize(text: str) -> str:
    """lowercase, Satzzeichen raus, mehrfache Leerzeichen zusammenfassen."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokens(text: str) -> set[str]:
    """Wortmenge ohne Füllwörter, für den bedeutungsnäheren Vergleich in
    _token_similarity() -- ergänzt den reinen Zeichenvergleich unten."""
    return {w for w in _normalize(text).split() if w not in _STOPWORDS and len(w) > 1}


def _token_similarity(a: str, b: str) -> float:
    """
    Dice-Koeffizient auf Wortebene statt Zeichenebene: erkennt umgestellte
    Reihenfolge und weggelassene Füllwörter zuverlässig ("Kratzer unten
    rechts" vs. "Es gibt einen Kratzer unten rechts"), und über den simplen
    Teilstring-Check auch deutsche Komposita ("Katze" steckt in
    "Katzenaufkleber"). Ersetzt SequenceMatcher nicht, sondern ergänzt ihn --
    compare_secret_feature() nimmt jeweils den besseren der beiden Werte.

    Bewusste Grenze: das bleibt reiner Wortabgleich, kein Sprachverständnis.
    Ein Synonym ohne gemeinsame Wortbestandteile ("Katze" vs. "Hello Kitty")
    wird NICHT erkannt -- das könnte nur eine KI beurteilen, und genau die
    darf das geheime Merkmal nie zu Gesicht bekommen (siehe lernnotizen.md).
    """
    tokens_a, tokens_b = _tokens(a), _tokens(b)
    if not tokens_a or not tokens_b:
        return 0.0

    shared = sum(
        1 for wa in tokens_a
        if any(
            wa == wb or (len(wa) >= 4 and len(wb) >= 4 and (wa in wb or wb in wa))
            for wb in tokens_b
        )
    )
    return (2 * shared) / (len(tokens_a) + len(tokens_b))


def compare_secret_feature(guess: str, actual: str) -> bool:
    """
    Toleranter Ähnlichkeitsvergleich statt exaktem String-Vergleich -- verzeiht
    Tippfehler, andere Wortreihenfolge und weggelassene Füllwörter, verlangt
    aber weiterhin, dass der wesentliche Inhalt getroffen wird. Kombiniert
    zwei sich ergänzende Signale (reines Python, kein KI-Aufruf):
    Zeichenketten-Ähnlichkeit (gut bei Tippfehlern) und Wort-Ähnlichkeit
    (gut bei anderer Reihenfolge/Formulierung) -- der bessere Wert entscheidet.
    """
    if not guess or not actual:
        return False

    seq_ratio = SequenceMatcher(None, _normalize(guess), _normalize(actual)).ratio()
    token_ratio = _token_similarity(guess, actual)
    return max(seq_ratio, token_ratio) >= SIMILARITY_THRESHOLD


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
