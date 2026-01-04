import pytest
import os
import sys
from unittest.mock import patch
from flask import Flask

# Add project root to path so we can import backend.app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from backend.app import create_app

@pytest.fixture
def app():
    # Set necessary environment variables for testing
    os.environ['JWT_SECRET_KEY'] = 'test-secret'
    app = create_app()
    app.config['TESTING'] = True
    # Disable exception propagation so the error handler is called
    app.config['PROPAGATE_EXCEPTIONS'] = False
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_internal_error_logs_exception(app, client):
    """
    Test that the 500 error handler uses logger.exception to log the full stack trace.
    """
    # Create a route that raises an exception
    @app.route('/trigger_error')
    def trigger_error():
        raise Exception("Simulated Server Error")

    # Mock the logger
    # We mock app.logger because current_app proxies to it
    with patch.object(app.logger, 'exception') as mock_exception:
        # Trigger the error
        response = client.get('/trigger_error')

        # Verify response is 500
        assert response.status_code == 500
        assert response.json == {"error": "Internal server error"}

        # Verify logger.exception was called
        assert mock_exception.called, "logger.exception was expected to be called but wasn't."
        # Verify the message
        args, _ = mock_exception.call_args
        # The error passed to the handler is a generic 500 Internal Server Error wrapper
        assert "Server Error:" in args[0]
