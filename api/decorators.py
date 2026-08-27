from functools import wraps

from flask import session, jsonify


def login_required(view):
    """Standard-Flask-Idiom: schützt eine Route, verlangt eine aktive Session.
    Lebt bewusst in api/, nicht in services/ -- Flask-Code (session, jsonify)
    gehört laut Projektkonvention nicht in die Business-Logik-Schicht."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"status": "error", "message": "Bitte einloggen."}), 401
        return view(*args, **kwargs)
    return wrapped
