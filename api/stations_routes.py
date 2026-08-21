from flask import Blueprint, jsonify, request

from services.db import stations_collection

stations_bp = Blueprint('stations', __name__)


@stations_bp.route('/api/stations', methods=['GET'])
def get_stations():
    try:
        stations = list(stations_collection.find())
        for station in stations:
            station['_id'] = str(station['_id'])
        return jsonify(stations), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fehler beim Abrufen: {str(e)}"}), 500


@stations_bp.route('/api/stations/recommend', methods=['GET'])
def recommend_stations():
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({"status": "error", "message": "Kategorie angeben (?category=...)."}), 400

        station = stations_collection.find_one({"serves_category": category})

        if station:
            station['_id'] = str(station['_id'])
            return jsonify({"status": "success", "recommended_station": station}), 200

        backup_station = stations_collection.find_one({"name": "Zentrales Fundbüro Berlin"})
        if backup_station:
            backup_station['_id'] = str(backup_station['_id'])

        return jsonify({
            "status": "success",
            "message": "Keine spezifische Station für diese Kategorie gefunden.",
            "recommended_station": backup_station
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fehler bei der Empfehlung: {str(e)}"}), 500
