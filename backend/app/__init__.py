import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from logging.handlers import RotatingFileHandler

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    CORS(app, supports_credentials=True)
    app.config["JWT_SECRET_KEY"] = "yoursecretkey"
    jwt = JWTManager(app)

    from app.routes import main
    from app.auth import auth

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main, url_prefix='/api')

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

    @app.route("/")
    def embed():
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        text = request.json["text"]
        embedding = model.encode(text)
        return {"embedding": embedding.tolist()}
    def index():
        return jsonify({"status": "ok", "message": "Skill Gap Generator API is running!"})

    if not os.path.exists("logs"):
        os.mkdir("logs")

    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=10240, backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] in %(module)s: %(message)s"
        )
    )
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("App startup")

    return app