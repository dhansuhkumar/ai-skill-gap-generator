from flask import Flask, jsonify
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)  # 👈 Enable CORS for all routes
    from .routes import main
    app.register_blueprint(main)

    @app.route("/")
    def index():
        return jsonify({"status": "ok", "message": "Skill Gap Generator API is running!"})

    return app
