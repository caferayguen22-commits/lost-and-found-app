import json
from pathlib import Path

PROMPTS_PATH = Path(__file__).resolve().parent.parent / "prompts.json"

# Zeichen, die wie eigene Prompt-Tags aussehen könnten, neutralisiert.
_ESCAPE_MAP = {"<": "‹", ">": "›"}


def _load_prompts() -> dict:
    """Lädt alle Prompt-Vorlagen einmalig aus der JSON-Datei."""
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_PROMPTS = _load_prompts()


def escape_for_prompt(text) -> str:
    """
    Neutralisiert Zeichen, die wie eigene Prompt-Tags aussehen könnten (z.B.
    ein selbstgebautes "</nutzereingabe>"), damit Nutzereingaben strukturell
    nie aus ihrem <nutzereingabe>-Container im Prompt ausbrechen können --
    unabhängig davon, was der Text sonst enthält (Prompt-Injection-Schutz,
    siehe lernnotizen.md).
    """
    if not text:
        return text
    text = str(text)
    for char, replacement in _ESCAPE_MAP.items():
        text = text.replace(char, replacement)
    return text


def _format_other_items(other_items_list) -> str:
    """
    Baut den Kandidaten-Block für die KI explizit und sicher selbst, statt
    Pythons Standard-str()-Darstellung einer rohen Liste zu vertrauen (die
    weder escaped noch für die KI gut lesbar ist). Jeder Eintrag wird
    einzeln in <nutzereingabe>-Tags gepackt.
    """
    if not other_items_list:
        return "(keine offenen Meldungen dieser Kategorie)"

    lines = []
    for item in other_items_list:
        lines.append(
            f"- ID {item.get('id')}: <nutzereingabe>{escape_for_prompt(item.get('title'))}"
            f" -- {escape_for_prompt(item.get('description'))}"
            f" (Ort: {escape_for_prompt(item.get('location'))})</nutzereingabe>"
        )
    return "\n".join(lines)


def _escape_kwargs(kwargs: dict) -> dict:
    """Zentrale Stelle, an der ALLE nutzerbeeinflussten Prompt-Bausteine
    abgesichert werden -- die aufrufende Seite (api/items_routes.py) muss
    sich darum nicht kümmern und übergibt weiterhin einfach die rohen Werte."""
    escaped = dict(kwargs)
    for key in ("category", "title", "description", "corrected_location", "current_location"):
        if key in escaped:
            escaped[key] = escape_for_prompt(escaped[key])
    if "other_items_list" in escaped:
        escaped["other_items_list"] = _format_other_items(kwargs["other_items_list"])
    return escaped


def build_found_prompt(**kwargs) -> tuple[str, str]:
    """
    Erwartet als kwargs: category, title, description, corrected_location,
    current_location, other_items_list.
    Gibt (system_message, user_prompt) zurück.
    """
    template = _PROMPTS["found"]
    return template["system_message"], template["user_template"].format(**_escape_kwargs(kwargs))


def build_lost_prompt(**kwargs) -> tuple[str, str]:
    """
    Erwartet als kwargs: category, title, description, corrected_location,
    other_items_list.
    Gibt (system_message, user_prompt) zurück.
    """
    template = _PROMPTS["lost"]
    return template["system_message"], template["user_template"].format(**_escape_kwargs(kwargs))


def build_photo_analysis_prompt(**kwargs) -> tuple[str, str]:
    """
    Erwartet als kwargs: category. Der Bildinhalt selbst wird NICHT hier
    eingebettet (kein Text, kann nicht in <nutzereingabe>-Tags escaped
    werden) -- das Bild wird in services/photo_analysis_service.py separat
    als eigener content-Block neben diesem Text an die KI übergeben.
    Gibt (system_message, user_prompt) zurück.
    """
    template = _PROMPTS["photo_analysis"]
    return template["system_message"], template["user_template"].format(**_escape_kwargs(kwargs))
