from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

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

    @app.route("/")
    def index():
        return jsonify({"status": "ok", "message": "Skill Gap Generator API is running!"})

    return app