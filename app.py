import os

from flask import Flask

from services.db import init_db
from api.items_routes import items_bp
from api.stations_routes import stations_bp
from api.status_routes import status_bp
from api.auth_routes import auth_bp
from api.garage_routes import garage_bp

init_db()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

app.register_blueprint(items_bp)
app.register_blueprint(stations_bp)
app.register_blueprint(status_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(garage_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5003)
