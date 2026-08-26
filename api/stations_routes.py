from flask import Blueprint, jsonify, request

from services.stations_repository import get_all_stations, get_stations_by_category, get_station_by_name

stations_bp = Blueprint('stations', __name__)


@stations_bp.route('/api/stations', methods=['GET'])
def get_stations():
    try:
        stations = get_all_stations()
        return jsonify([station.to_dict() for station in stations]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fehler beim Abrufen: {str(e)}"}), 500


@stations_bp.route('/api/stations/recommend', methods=['GET'])
def recommend_stations():
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({"status": "error", "message": "Kategorie angeben (?category=...)."}), 400

        matches = get_stations_by_category(category)
        if matches:
            return jsonify({"status": "success", "recommended_station": matches[0].to_dict()}), 200

        backup_station = get_station_by_name("Zentrales Fundbüro Berlin")
        return jsonify({
            "status": "success",
            "message": "Keine spezifische Station für diese Kategorie gefunden.",
            "recommended_station": backup_station.to_dict() if backup_station else None
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fehler bei der Empfehlung: {str(e)}"}), 500
