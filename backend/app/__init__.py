import os
import logging
from flask import Flask, jsonify, request # Removed 'app' from import, it's the Flask instance
from flask_cors import CORS
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

# Optional phase2 routes may not exist in the committed tree (guard import)
phase2_bp = None
try:
    from backend.routes_phase2 import bp as phase2_bp
except ImportError as e:
    try:
        from routes_phase2 import bp as phase2_bp
    except ImportError as e2:
        logging.warning(f"Phase 2 routes could not be imported: {e} / {e2}")
        phase2_bp = None

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

_embedding_model = None

def create_app():
    app = Flask(__name__)
    
    # Security: Request size limits
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
    app.config['JSON_SORT_KEYS'] = False  # Prevent JSON key sorting for consistency
    
    # Configure CORS - Use environment variable or default to local dev ports
    # Security: Don't allow wildcard origins with credentials
    flask_env = os.getenv("FLASK_ENV", "development")
    is_production = flask_env == "production"
    
    if is_production:
        # Production: Use explicitly configured origins only
        raw_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
        if not raw_origins:
            logging.warning("CORS_ALLOWED_ORIGINS not set in production - CORS will be restrictive")
            allowed_origins = []
        elif raw_origins == "*":
            logging.error("CORS_ALLOWED_ORIGINS=* is NOT allowed in production with credentials!")
            raise RuntimeError("Wildcard CORS origin is not allowed in production with credentials enabled")
        else:
            allowed_origins = [origin.strip() for origin in raw_origins.split(',') if origin.strip()]
    else:
        # Development: Allow local dev servers
        raw_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5174,http://localhost:5173,http://127.0.0.1:5174,http://127.0.0.1:5173")
        allowed_origins = [origin.strip() for origin in raw_origins.split(',') if origin.strip()]
    
    logging.info(f"CORS allowed origins: {allowed_origins}")

    # Initialize CORS with comprehensive settings for Supabase JWT auth
    CORS(
        app,
        origins=allowed_origins,
        supports_credentials=True,
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "X-Requested-With",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
        ],
        expose_headers=[
            "Content-Type",
            "Authorization",
            "X-Request-Id",
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        max_age=600,  # Cache preflight requests for 10 minutes
    )




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

    # Supabase config - Backend uses SUPABASE_URL/KEY (no VITE_ prefix)
    app.config["SUPABASE_URL"] = os.getenv("SUPABASE_URL")
    app.config["SUPABASE_KEY"] = os.getenv("SUPABASE_KEY")

    # Supabase is REQUIRED for authentication
    if not app.config["SUPABASE_URL"] or not app.config["SUPABASE_KEY"]:
        logging.critical("CRITICAL: Supabase credentials not configured")
        raise RuntimeError(
            "Supabase is required. "
            "Set SUPABASE_URL and SUPABASE_KEY in your .env file."
        )

    if not _get_supabase_func_app:
        logging.critical("Supabase client module not found")
        raise RuntimeError("Supabase client module (supabase_client.py) not found")
    
    try:
        app.supabase = _get_supabase_func_app()
        if not app.supabase:
            logging.critical("Supabase client initialization returned None")
            raise RuntimeError("Failed to initialize Supabase client")
        logging.info("Supabase client initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize Supabase: {e}")
        raise RuntimeError(f"Supabase initialization failed: {e}")


    from .routes import main
    from .auth import auth
    from .dashboard_routes import dashboard

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main, url_prefix='/api')
    app.register_blueprint(dashboard, url_prefix='/api')
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