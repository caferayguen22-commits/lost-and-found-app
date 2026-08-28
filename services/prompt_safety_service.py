import re

# Bewusst eine kleine, klar begrenzte Liste klassischer Injection-Phrasen --
# das ist ein Monitoring-Signal, keine Verteidigung für sich (siehe
# lernnotizen.md: Keyword-Erkennung ist leicht umgehbar durch Umformulierung,
# andere Sprache, Unicode-Tricks). Die eigentliche Absicherung sind die
# <nutzereingabe>-Tags + escape_for_prompt() in services/prompt_service.py.
_SUSPICIOUS_PATTERNS = [
    r"ignor[a-zäöü]*\s+(alle|vorherige[nr]?|obige[nr]?)\s+anweisung",
    r"disregard\s+(the\s+)?(above|previous)\s+instructions?",
    r"ignore\s+(all\s+|previous\s+|above\s+|the\s+)*instructions?",
    r"\bsystem\s*:",
    r"\bneue\s+anweisung(en)?\b",
    r"\bnew\s+instructions?\b",
    r"setze\s+match_found",
    r"set\s+match_found",
    r"\byou\s+are\s+now\b",
    r"\bdu\s+bist\s+jetzt\b",
]

_COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in _SUSPICIOUS_PATTERNS]


def contains_suspicious_pattern(text: str) -> bool:
    """
    Leichte Heuristik, die klassische Prompt-Injection-Formulierungen erkennt
    -- NUR fürs Logging/Monitoring gedacht, blockiert bewusst nichts (zu viele
    plausible Fehlalarme bei harmlosem Text). Kein Ersatz für die strukturelle
    Absicherung in prompt_service.py.
    """
    if not text:
        return False
    return any(pattern.search(text) for pattern in _COMPILED_PATTERNS)
