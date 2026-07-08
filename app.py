from flask import Flask, jsonify

# Initialisierung der Flask-Applikation
app = Flask(__name__)

# Test-Route zur Überprüfung, ob der Server läuft
@app.route('/')
def home():
    return jsonify({
        "status": "erfolgreich",
        "nachricht": "Willkommen bei der Community Lost & Found App!"
    })

# Start des lokalen Entwicklungsservers
if __name__ == '__main__':
    app.run(debug=True, port=5000)