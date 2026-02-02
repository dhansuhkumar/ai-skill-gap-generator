"""
Centralized logging configuration for the AI Skill Gap Generator.
Prevents duplicate handlers and ensures consistent logging across all modules.
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_level=None):
    """
    Configure application-wide logging.
    
    Args:
        log_level: Optional logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If not provided, uses LOG_LEVEL environment variable or defaults to INFO
    
    Returns:
        Configured root logger
    """
    # Determine log level
    if log_level is None:
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, env_level, logging.INFO)
    
    # Remove existing handlers to prevent duplicates
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    
    # Create console handler with UTF-8 encoding (Windows fix)
    console_handler = logging.StreamHandler(sys.stdout)
    # Force UTF-8 encoding on Windows to handle emoji/special characters
    if hasattr(console_handler.stream, 'buffer'):
        import io
        console_handler.stream = io.TextIOWrapper(
            console_handler.stream.buffer,
            encoding='utf-8',
            errors='replace'
        )
    
    # Create formatter (avoid emoji in production logs for Windows compatibility)
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create file handler with rotation
    log_file = log_dir / "application.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root.addHandler(console_handler)
    root.addHandler(file_handler)
    root.setLevel(log_level)
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    
    logging.info(f"Logging configured (Level: {logging.getLevelName(log_level)})")
    
    return root


def get_logger(name):
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Usually __name__ from the calling module
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
