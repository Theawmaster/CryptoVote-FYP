import os
import sys
import pytest
from flask import Flask, jsonify
from unittest.mock import patch, MagicMock

# Dynamically add backend to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from routes.register import register_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(register_bp, url_prefix="/register")
    app.config["TESTING"] = True
    return app.test_client()

# ----------- /register/ (POST) ------------

@patch("routes.register.handle_registration")
def test_register_valid_email(mock_handler, client):
    mock_handler.return_value = ("Registered", 201)
    response = client.post("/register/", json={"email": "user@e.ntu.edu.sg"})
    assert response.status_code == 201
    mock_handler.assert_called_once_with("user@e.ntu.edu.sg", "voter")

@patch("routes.register.handle_registration")
def test_register_invalid_email_format(mock_handler, client):
    with client.application.app_context():
        mock_handler.return_value = (
            jsonify({"error": "Invalid email domain"}), 400
        )
        response = client.post("/register/", json={"email": "hacker@gmail.com"})
        assert response.status_code == 400
        assert "Invalid email domain" in response.get_json()["error"]

@patch("routes.register.handle_registration")
def test_register_missing_email(mock_handler, client):
    with client.application.app_context():
        mock_handler.return_value = (
            jsonify({"error": "Email is required"}), 400
        )
        response = client.post("/register/", json={})
        assert response.status_code == 400
        assert "Email is required" in response.get_json()["error"]

# ----------- /verify-email (GET) ------------

def test_verify_email_missing_token(client):
    response = client.get("/register/verify-email")
    assert response.status_code == 400
    assert "token" in response.get_json()["error"]

@patch("routes.register.Voter")
def test_verify_email_invalid_token(mock_voter_class, client):
    mock_voter_class.query.filter_by.return_value.first.return_value = None
    response = client.get("/register/verify-email?token=invalid123")
    assert response.status_code == 404
    assert "Invalid or expired token" in response.get_json()["error"]

@patch("routes.register.db")
@patch("routes.register.pyotp.TOTP")
@patch("routes.register.Voter")
def test_verify_email_success(mock_voter_class, mock_totp, mock_db, client):
    mock_voter = MagicMock(email_hash="hash123")
    mock_voter_class.query.filter_by.return_value.first.return_value = mock_voter
    mock_totp.return_value.provisioning_uri.return_value = "otpauth://totp/CryptoVote"

    response = client.get("/register/verify-email?token=validtoken123")
    assert response.status_code == 200
    assert "Email verified" in response.get_json()["message"]
    assert "totp_uri" in response.get_json()
