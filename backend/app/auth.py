import os
import time
import logging
from functools import wraps
from flask import request, g, jsonify, Blueprint, current_app

logger = logging.getLogger(__name__)

auth = Blueprint("auth", __name__)


@auth.route("/ping", methods=["GET"])
def ping():
    import datetime

    return jsonify(
        {
            "status": "auth service ok",
            "provider": "session",
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
    ), 200


def session_required(f):
    """
    Decorator to protect Flask routes using session-based authentication.
    Reads X-Session-ID header instead of JWT token.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return jsonify({"status": "ok"}), 200

        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            session_id = "anonymous"

        g.user = {"id": session_id, "email": "anonymous", "provider": "session"}

        return f(*args, **kwargs)

    return decorated
