import json
from pathlib import Path

PROMPTS_PATH = Path(__file__).resolve().parent.parent / "prompts.json"


def _load_prompts() -> dict:
    """Lädt alle Prompt-Vorlagen einmalig aus der JSON-Datei."""
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_PROMPTS = _load_prompts()


def build_found_prompt(**kwargs) -> tuple[str, str]:
    """
    Erwartet als kwargs: category, title, description, raw_location,
    current_location, lost_items_list, stations_list.
    Gibt (system_message, user_prompt) zurück.
    """
    template = _PROMPTS["found"]
    return template["system_message"], template["user_template"].format(**kwargs)


def build_lost_prompt(**kwargs) -> tuple[str, str]:
    """
    Erwartet als kwargs: category, title, description, corrected_location.
    Gibt (system_message, user_prompt) zurück.
    """
    template = _PROMPTS["lost"]
    return template["system_message"], template["user_template"].format(**kwargs)