import json
import logging

from flask import Blueprint, jsonify, request
from openai import OpenAIError

from services.photo_analysis_service import analyze_photo, UnsupportedImageFormatError
from services.photo_analysis_repository import record_attempt, count_recent_attempts

photo_bp = Blueprint('photo', __name__)
logger = logging.getLogger(__name__)

# Grosszuegiger als das geheime-Merkmal-Rate-Limit (5/30min), da harmlos bei
# Mehrfachnutzung -- aber der Endpoint ist ohne Login erreichbar und jeder
# Aufruf kostet echtes Geld (Vision-Modell), daher trotzdem begrenzt.
RATE_LIMIT_MAX_ATTEMPTS = 20
RATE_LIMIT_WINDOW_MINUTES = 60


@photo_bp.route('/api/analyze-photo', methods=['POST'])
def analyze_photo_route():
    data = request.get_json()
    if not data or not data.get('image'):
        return jsonify({"status": "error", "message": "Kein Foto übergeben."}), 400

    ip_address = request.remote_addr or 'unknown'
    if count_recent_attempts(ip_address, RATE_LIMIT_WINDOW_MINUTES) >= RATE_LIMIT_MAX_ATTEMPTS:
        return jsonify({
            "status": "error",
            "message": "Zu viele Foto-Analysen. Bitte später erneut probieren."
        }), 429

    record_attempt(ip_address)

    try:
        result = analyze_photo(data['image'], data.get('category'))
    except UnsupportedImageFormatError as e:
        return jsonify({
            "status": "error",
            "message": (
                f"Dieses Bildformat ({e.mime_type}) wird von der Foto-Analyse leider nicht "
                "unterstützt -- häufig bei HEIC-Fotos vom iPhone. Bitte wähle ein JPEG- oder "
                "PNG-Foto (z.B. beim Teilen/Exportieren 'Als JPEG' wählen, oder einen "
                "Screenshot des Fotos hochladen)."
            )
        }), 400
    except OpenAIError as oe:
        logger.warning("Foto-Analyse fehlgeschlagen (OpenAI-Fehler): %s", oe)
        return jsonify({"status": "error", "message": "Foto-Analyse derzeit nicht verfügbar."}), 502
    except json.JSONDecodeError:
        logger.warning("Foto-Analyse: KI-Antwort war kein valides JSON.")
        return jsonify({"status": "error", "message": "KI-Antwort konnte nicht verarbeitet werden."}), 502

    return jsonify({
        "status": "success",
        "sufficient_detail": bool(result.get("sufficient_detail")),
        "guidance_hint": result.get("guidance_hint"),
        "brand": result.get("brand"),
        "model": result.get("model"),
        "color": result.get("color"),
        "other_features": result.get("other_features"),
        "condition_description": result.get("condition_description"),
        "suggested_title": result.get("suggested_title"),
        "suggested_description": result.get("suggested_description"),
    }), 200
