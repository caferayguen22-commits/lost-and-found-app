import json

from services.db import openai_client
from services.prompt_service import build_photo_analysis_prompt

# gpt-4o-mini ist vision-fähig und wird bereits fürs Matching genutzt (Konsistenz).
# "high" statt "low" Detail, weil der Kernzweck (Typenschild/Modellbezeichnung lesen)
# gerade feine Details braucht -- der Kostenunterschied ist bei diesem Modell
# ohnehin gering (siehe lernnotizen.md).
VISION_MODEL = "gpt-4o-mini"
IMAGE_DETAIL = "high"

# Von OpenAIs Vision-Modellen unterstützte Bildformate (Stand 2026). HEIC/HEIF
# (Standardformat auf iPhone/Mac) gehört bewusst NICHT dazu -- ohne diese
# Prüfung würde das erst als kryptischer 502 vom OpenAI-Aufruf auffallen.
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}


class UnsupportedImageFormatError(Exception):
    """Bildformat wird von OpenAIs Vision-Modellen nicht unterstützt (z.B.
    HEIC/HEIF) -- api/photo_routes.py macht daraus eine verständliche
    Fehlermeldung statt eines rohen 502."""

    def __init__(self, mime_type: str | None):
        self.mime_type = mime_type
        super().__init__(mime_type or "unbekanntes Format")


def _extract_mime_type(image_data_url: str) -> str | None:
    """Liest den MIME-Type aus einer 'data:image/xyz;base64,...'-URL (so wie
    sie der Browser per FileReader.readAsDataURL erzeugt)."""
    if not image_data_url.startswith("data:"):
        return None
    header = image_data_url.split(",", 1)[0]  # z.B. "data:image/heic;base64"
    return header[len("data:"):].split(";")[0].lower() or None


def analyze_photo(image_data_url: str, category: str | None) -> dict:
    """
    Ein-Schuss-KI-Aufruf über den rohen openai-Client (wie Zusammenfassung/
    Rechtschreibkorrektur, siehe CLAUDE.md) -- bewusst NICHT Teil des
    LangGraph-Matching-Ablaufs, da die Foto-Analyse unabhängig vom Matching
    ist und zeitlich VOR dem Anlegen eines Items läuft (siehe api/photo_routes.py).
    Gibt das geparste JSON-Dict der KI-Antwort zurück (Format siehe
    prompts.json -> "photo_analysis").
    """
    mime_type = _extract_mime_type(image_data_url)
    if mime_type and mime_type not in SUPPORTED_IMAGE_TYPES:
        raise UnsupportedImageFormatError(mime_type)

    system_message, user_text = build_photo_analysis_prompt(category=category or "unbekannt")

    response = openai_client.chat.completions.create(
        model=VISION_MODEL,
        response_format={"type": "json_object"},
        timeout=20.0,
        messages=[
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url, "detail": IMAGE_DETAIL},
                    },
                ],
            },
        ],
    )
    return json.loads(response.choices[0].message.content)
