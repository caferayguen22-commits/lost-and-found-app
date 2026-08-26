from flask import Flask

from services.db import init_db
from api.items_routes import items_bp
from api.stations_routes import stations_bp
from api.status_routes import status_bp

init_db()

app = Flask(__name__)

app.register_blueprint(items_bp)
app.register_blueprint(stations_bp)
app.register_blueprint(status_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5003)
