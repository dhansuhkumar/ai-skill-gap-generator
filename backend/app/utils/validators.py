"""
Input validation utilities for the application.
"""
import re
from functools import wraps
from flask import request, jsonify

# Password requirements: 8+ chars, 1 uppercase, 1 lowercase, 1 digit, 1 special
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

# Email validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Max file size for uploads (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}


def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format."""
    if not email:
        return False, "Email is required"
    if len(email) > 254:
        return False, "Email too long"
    if not EMAIL_REGEX.match(email):
        return False, "Invalid email format"
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if not password:
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if len(password) > 128:
        return False, "Password too long"
    if not PASSWORD_REGEX.match(password):
        return False, "Password must contain uppercase, lowercase, digit, and special character"
    return True, ""


def validate_file_extension(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename to prevent path traversal."""
    # Remove path components = filename
    filename.split('/')[-1].split('\\')[-1]
    # Remove special characters except alphanumeric, underscore, hyphen, dot
    filename = re.sub(r'[^\w\-\.]', '', filename)
    # Limit length
    return filename[:100] if filename else 'uploaded_file'


def require_json(f):
    """Decorator to require JSON content type."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        return f(*args, **kwargs)
    return decorated


def validate_request_data(required_fields: list, optional_fields: list = None):
    """
    Decorator to validate request JSON data.
    required_fields: list of field names that must be present
    optional_fields: list of allowed optional field names
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json(silent=True)
            if not data:
                return jsonify({"error": "Invalid JSON body"}), 400
            
            # Check required fields
            missing = [field for field in required_fields if field not in data or data[field] is None]
            if missing:
                return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
            
            # Check for unknown fields
            if optional_fields:
                unknown = [field for field in data.keys() if field not in required_fields and field not in optional_fields]
                if unknown:
                    return jsonify({"error": f"Unknown fields: {', '.join(unknown)}"}), 400
            
            return f(*args, **kwargs)
        return decorated
    return decorator
