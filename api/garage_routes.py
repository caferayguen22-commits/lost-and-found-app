from flask import Blueprint, jsonify, request, render_template, session, redirect

from api.decorators import login_required
from services.garage_items_repository import (
    insert_garage_item, get_garage_items_by_user, update_status, delete_garage_item,
    find_by_identifying_marks, record_check_attempt, count_recent_check_attempts
)
from models.garage_item import GarageItem

garage_bp = Blueprint('garage', __name__)

VALID_STATUSES = {'safe', 'lost', 'stolen'}
STATUS_PRIORITY = {'stolen': 2, 'lost': 1, 'safe': 0}

CHECK_RATE_LIMIT_MAX_ATTEMPTS = 20
CHECK_RATE_LIMIT_WINDOW_MINUTES = 60


@garage_bp.route('/garage')
def garage_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('garage.html')


@garage_bp.route('/garage/check')
def garage_check_page():
    return render_template('garage_check.html')


@garage_bp.route('/api/garage', methods=['POST'])
@login_required
def create_garage_item():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Keine Daten übergeben."}), 400

    title = data.get('title')
    description = data.get('description')
    if not title or not description:
        return jsonify({"status": "error", "message": "Titel und Beschreibung sind Pflichtfelder."}), 400

    item = GarageItem(
        user_id=session['user_id'],
        category=data.get('category', 'Sonstiges'),
        title=title,
        description=description,
        identifying_marks=data.get('identifying_marks'),
        image=data.get('image')
    )
    new_item = insert_garage_item(item)
    return jsonify({"status": "success", "message": "Gegenstand registriert.", "item": new_item.to_dict()}), 201


@garage_bp.route('/api/garage', methods=['GET'])
@login_required
def list_garage_items():
    items = get_garage_items_by_user(session['user_id'])
    return jsonify([item.to_dict() for item in items]), 200


@garage_bp.route('/api/garage/<int:item_id>/status', methods=['POST'])
@login_required
def change_status(item_id):
    data = request.get_json()
    new_status = data.get('status') if data else None
    if new_status not in VALID_STATUSES:
        return jsonify({"status": "error", "message": "Ungültiger Status."}), 400

    if update_status(item_id, session['user_id'], new_status):
        return jsonify({"status": "success", "message": "Status aktualisiert."}), 200
    return jsonify({"status": "error", "message": "Gegenstand wurde nicht gefunden."}), 404


@garage_bp.route('/api/garage/<int:item_id>', methods=['DELETE'])
@login_required
def delete_garage_item_route(item_id):
    if delete_garage_item(item_id, session['user_id']):
        return jsonify({"status": "success", "message": "Gegenstand gelöscht."}), 200
    return jsonify({"status": "error", "message": "Gegenstand wurde nicht gefunden."}), 404


@garage_bp.route('/api/garage/check', methods=['POST'])
def check_garage_item():
    """Öffentliche Prüf-Funktion für Käufer -- kein Login nötig, aber auch
    keine Möglichkeit, Garagen zu durchsuchen/aufzulisten: nur ein gezielter
    Treffer auf eine konkrete Seriennummer/ein Merkmal. Gibt niemals Besitzer-
    Identität oder identifying_marks zurück (siehe GarageItem.to_public_dict)."""
    data = request.get_json()
    marks = (data.get('identifying_marks') or '').strip() if data else ''
    if not marks:
        return jsonify({"status": "error", "message": "Bitte eine Seriennummer/ein Merkmal angeben."}), 400

    ip_address = request.remote_addr or 'unknown'
    if count_recent_check_attempts(ip_address, CHECK_RATE_LIMIT_WINDOW_MINUTES) >= CHECK_RATE_LIMIT_MAX_ATTEMPTS:
        return jsonify({"status": "error", "message": "Zu viele Anfragen. Bitte später erneut probieren."}), 429

    record_check_attempt(ip_address)
    matches = find_by_identifying_marks(marks)

    if not matches:
        return jsonify({"status": "success", "found": False}), 200

    # Bei (theoretisch) mehreren Treffern den "schlimmsten" Status anzeigen.
    worst = max(matches, key=lambda i: STATUS_PRIORITY[i.status])
    return jsonify({"status": "success", "found": True, "item": worst.to_public_dict()}), 200
