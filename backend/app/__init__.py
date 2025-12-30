import os
import logging
from flask import Flask, jsonify, request # Removed 'app' from import, it's the Flask instance
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

# Optional phase2 routes may not exist in the committed tree (guard import)
phase2_bp = None
try:
    from backend.routes_phase2 import bp as phase2_bp
except ImportError: # Use ImportError here
    try:
        from routes_phase2 import bp as phase2_bp
    except ImportError: # Use ImportError here
        phase2_bp = None

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

_embedding_model = None

def create_app():
    app = Flask(__name__)

    # Allow requests specifically from your frontend dev server
    CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://localhost:5000"]}}, supports_credentials=True)

    # Configure logging
    log_file_path = os.path.join(os.getcwd(), 'logs', 'app.log')
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    file_handler = RotatingFileHandler(log_file_path, maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)

    # Add console handler for stdout in production/container environments
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    console_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup...')

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Configure CORS - Production Hardening
    allowed_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    if allowed_origins_str == "*":
        app.logger.warning("CORS_ALLOWED_ORIGINS is set to '*' - This is insecure for production!")
        allowed_origins = ["*"]
    else:
        allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]
        app.logger.info(f"CORS_ALLOWED_ORIGINS set to: {allowed_origins}")

    CORS(app, resources={r"/*": {"origins": allowed_origins}}, supports_credentials=True)
    # ✅ SECURE: Read secret from .env
    jwt_secret_key = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret_key:
        raise RuntimeError("FATAL: JWT_SECRET_KEY environment variable is not set. Aborting startup for security.")
    app.config["JWT_SECRET_KEY"] = jwt_secret_key
    jwt = JWTManager(app)

    # Store the loaded embedding model in app.config
    app.config['EMBEDDING_MODEL'] = _embedding_model

    # Attach Supabase client (if configured) to the app for use in routes
    _get_supabase_func_app = None
    try:
        from backend.supabase_client import get_supabase as _get_supabase_func_app
    except ImportError:
        try:
            from supabase_client import get_supabase as _get_supabase_func_app
        except ImportError:
            _get_supabase_func_app = None

    app.supabase = None # Default to None
    if _get_supabase_func_app:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if supabase_url and supabase_key:
            try:
                app.supabase = _get_supabase_func_app()
                logging.info("Supabase client attached to app successfully.")
            except Exception as e:
                logging.error(f"Error attaching Supabase client to app: {e}")
                # If Supabase is configured but fails here, run.py should have already raised a RuntimeError
                # So here we just log and app.supabase remains None
        else:
            logging.info("Supabase client module found but not configured (SUPABASE_URL or SUPABASE_KEY missing).")
    else:
        logging.info("Supabase client module not found for app.")


    from .routes import main
    from .auth import auth

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main, url_prefix='/api')
    if phase2_bp:
        app.register_blueprint(phase2_bp, url_prefix="/api")


    # ✅ Root route - just shows API status
    @app.route("/", methods=["GET"])
    def index():
      return jsonify({"status": "ok", "message": "Skill Gap Generator API is running!"})

    # ✅ Status route for health check
    @app.route("/status", methods=["GET"])
    def status():
      return jsonify({"status": "ok"})


    # ✅ Optional: Only define this separate endpoint for embeddings
    @app.route("/api/embed", methods=["POST"])
    def embed():
        # Use the pre-loaded model from app.config
        model = app.config['EMBEDDING_MODEL']
        if not model:
            return jsonify({"error": "Embedding service not available (model not loaded)"}), 503

        data = request.get_json(silent=True)
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' in request body"}), 400

        embedding = model.encode(data["text"])
        return jsonify({"embedding": embedding.tolist()})

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "message": "Application is running"}), 200

    @app.route("/ready", methods=["GET"])
    def ready():
        issues = []

        # Check embedding model readiness
        if not app.config.get('EMBEDDING_MODEL'):
            issues.append("Embedding model not loaded")

        # Check Supabase connection if configured
        if app.supabase:
            try:
                # A simple Supabase call to check connection
                # This might need adjustment based on the actual Supabase client's method for a lightweight check
                app.supabase.from_("auth_users").select("id").limit(1).execute()
            except Exception as e:
                issues.append(f"Supabase connection failed: {e}")
        elif os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
            issues.append("Supabase is configured but client not initialized or connected")
        # If no Supabase config, assume local SQLite is used and ready.

        if issues:
            return jsonify({"status": "not ready", "issues": issues}), 503
        return jsonify({"status": "ready", "message": "All critical services are ready"}), 200

    return app