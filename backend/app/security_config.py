"""
Security configuration for production deployment.
Implements security headers and rate limiting.
"""
import os
from functools import wraps
from flask import request, jsonify
from time import time
from collections import defaultdict


# ==================== SECURITY HEADERS ====================

def add_security_headers(response):
    """
    Add security headers to all responses.
    
    Implements OWASP recommended security headers:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filter
    - Strict-Transport-Security: Force HTTPS (production only)
    - Content-Security-Policy: Restrict resource loading
    """
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Enable XSS filter (legacy browsers)
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Force HTTPS in production
    flask_env = os.getenv('FLASK_ENV', 'development')
    if flask_env == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy (adjust as needed)
    # This is a restrictive policy - you may need to adjust for your frontend
    csp = "default-src 'self'; " \
          "script-src 'self' 'unsafe-inline' 'unsafe-eval'; " \
          "style-src 'self' 'unsafe-inline'; " \
          "img-src 'self' data: https:; " \
          "font-src 'self' data:; " \
          "connect-src 'self' https://kquhgkomsqlbqjigxmiz.supabase.co https://www.googleapis.com;"
    
    response.headers['Content-Security-Policy'] = csp
    
    return response


# ==================== RATE LIMITING ====================

# Simple in-memory rate limiter
# For production, consider using Redis or a dedicated rate limiting service
_rate_limit_storage = defaultdict(list)
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX_REQUESTS = 60  # requests per window


def rate_limit(max_requests=None, window=None):
    """
    Decorator to rate limit API endpoints.
    
    Args:
        max_requests: Maximum requests allowed in the time window
        window: Time window in seconds
    
    Returns:
        Decorated function with rate limiting
    """
    max_reqs = max_requests or _RATE_LIMIT_MAX_REQUESTS
    time_window = window or _RATE_LIMIT_WINDOW
    
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get client identifier (IP address or user ID)
            identifier = request.remote_addr
            
            # Get current timestamp
            now = time()
            
            # Clean old requests outside the window
            _rate_limit_storage[identifier] = [
                timestamp for timestamp in _rate_limit_storage[identifier]
                if now - timestamp < time_window
            ]
            
            # Check if rate limit exceeded
            if len(_rate_limit_storage[identifier]) >= max_reqs:
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {int(time_window)} seconds."
                }), 429
            
            # Add current request timestamp
            _rate_limit_storage[identifier].append(now)
            
            # Execute the actual function
            return f(*args, **kwargs)
        
        return wrapped
    return decorator


# ==================== INPUT SANITIZATION ====================

def sanitize_input(data):
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        data: Input data (string, dict, list)
    
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        # Remove potential SQL injection characters
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            data = data.replace(char, '')
        return data.strip()
    
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    
    return data


# ==================== FILE UPLOAD VALIDATION ====================

ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB


def allowed_file(filename):
    """
    Check if file extension is allowed.
    
    Args:
        filename: Name of the file
    
    Returns:
        Boolean indicating if file is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_upload(file):
    """
    Validate uploaded file.
    
    Args:
        file: File object from request
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "Empty filename"
    
    if not allowed_file(file.filename):
        return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size (if available)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to start
    
    if size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    return True, None
