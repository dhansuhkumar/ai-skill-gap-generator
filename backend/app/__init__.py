import os
import logging
from xml.parsers.expat import model
from flask import Flask, app, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

from backend.routes_phase2 import bp as phase2_bp

from torch import embedding

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    CORS(app, supports_credentials=True)
    # ✅ SECURE: Read secret from .env
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    jwt = JWTManager(app)

    from app.routes import main
    from app.auth import auth

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main, url_prefix='/api')
    app.register_blueprint(phase2_bp, url_prefix="/api")



    # ✅ Root route - just shows API status
    @app.route("/", methods=["GET"])
    def index():
      return jsonify({"status": "ok", "message": "Skill Gap Generator API is running!"})


# ✅ Optional: Only define this separate endpoint for embeddings
    @app.route("/api/embed", methods=["POST"])
    def embed():
        from sentence_transformers import SentenceTransformer
        data = request.get_json(silent=True)
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' in request body"}), 400

        model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding = model.encode(data["text"])
        return jsonify({"embedding": embedding.tolist()})

    return app