from flask import Blueprint, jsonify, request, render_template, session

from services.auth_service import hash_password, verify_password, is_valid_email, is_valid_password
from services.users_repository import insert_user, get_user_by_email, get_user_by_id
from models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register')
def register_page():
    return render_template('register.html')


@auth_bp.route('/login')
def login_page():
    return render_template('login.html')


@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Keine Daten übergeben."}), 400

    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not is_valid_email(email):
        return jsonify({"status": "error", "message": "Bitte eine gültige E-Mail-Adresse angeben."}), 400
    if not is_valid_password(password):
        return jsonify({"status": "error", "message": "Passwort muss mindestens 8 Zeichen lang sein."}), 400
    if get_user_by_email(email):
        return jsonify({"status": "error", "message": "Diese E-Mail-Adresse ist bereits registriert."}), 409

    user = insert_user(User(email=email, password_hash=hash_password(password)))
    session['user_id'] = user.id

    return jsonify({"status": "success", "message": "Registrierung erfolgreich.", "user": user.to_dict()}), 201


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Keine Daten übergeben."}), 400

    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    user = get_user_by_email(email)
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"status": "error", "message": "E-Mail oder Passwort ist falsch."}), 401

    session['user_id'] = user.id
    return jsonify({"status": "success", "message": "Login erfolgreich.", "user": user.to_dict()}), 200


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"status": "success", "message": "Ausgeloggt."}), 200


@auth_bp.route('/api/me', methods=['GET'])
def me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "success", "logged_in": False}), 200

    user = get_user_by_id(user_id)
    if not user:
        # Session verweist auf einen nicht mehr existierenden User -- Session bereinigen.
        session.pop('user_id', None)
        return jsonify({"status": "success", "logged_in": False}), 200

    return jsonify({"status": "success", "logged_in": True, "user": user.to_dict()}), 200
