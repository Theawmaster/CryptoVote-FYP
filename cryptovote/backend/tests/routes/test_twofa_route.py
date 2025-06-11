import os
import sys
import pytest
from flask import Flask, jsonify
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add backend path dynamically
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from routes.twofa import otp_bp, otp_cooldown

@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"  # required for session
    app.register_blueprint(otp_bp)
    app.config["TESTING"] = True
    with app.app_context():
        yield app.test_client()

def test_missing_email_or_otp(client):
    response = client.post("/2fa-verify", json={})
    assert response.status_code == 400
    assert "Email and OTP are required" in response.get_json()["error"]


@patch("routes.twofa.Voter")
def test_user_not_logged_in(mock_voter_class, client):
    mock_voter_class.query.filter_by.return_value.first.return_value = None
    response = client.post("/2fa-verify", json={"email": "user@e.ntu.edu.sg", "otp": "123456"})
    assert response.status_code == 403
    assert "not logged in" in response.get_json()["error"]


@patch("routes.twofa.Voter")
def test_cooldown_block(mock_voter_class, client):
    voter = MagicMock()
    voter.logged_in = True
    mock_voter_class.query.filter_by.return_value.first.return_value = voter

    email_hash = "mockedhash"
    with patch("routes.twofa.hashlib.sha256") as mock_hash:
        mock_hash.return_value.hexdigest.return_value = email_hash
        otp_cooldown[email_hash] = datetime.utcnow()

        response = client.post("/2fa-verify", json={"email": "test@e.ntu.edu.sg", "otp": "000000"})
        assert response.status_code == 429
        assert "Too many attempts" in response.get_json()["error"]

@patch("routes.twofa.db")
@patch("routes.twofa.pyotp.TOTP")
@patch("routes.twofa.Voter")
def test_successful_2fa(mock_voter_class, mock_totp_class, mock_db, client):
    voter = MagicMock()
    voter.logged_in = True
    voter.totp_secret = "base32secret"
    voter.email_hash = "testhash"
    voter.vote_role = "voter" 
    mock_voter_class.query.filter_by.return_value.first.return_value = voter

    totp_instance = MagicMock()
    totp_instance.verify.return_value = True
    mock_totp_class.return_value = totp_instance

    with client.session_transaction() as sess:
        sess["email"] = "test@e.ntu.edu.sg"

    response = client.post("/2fa-verify", json={"email": "test@e.ntu.edu.sg", "otp": "123456"})
    assert response.status_code == 200
    assert "2FA successful" in response.get_json()["message"]
    assert mock_db.session.commit.called

@patch("routes.twofa.pyotp.TOTP")
@patch("routes.twofa.Voter")
def test_invalid_otp(mock_voter_class, mock_totp_class, client):
    voter = MagicMock()
    voter.logged_in = True
    voter.totp_secret = "base32secret"
    mock_voter_class.query.filter_by.return_value.first.return_value = voter

    totp_instance = MagicMock()
    totp_instance.verify.return_value = False
    mock_totp_class.return_value = totp_instance

    email_hash = "testhash"
    with patch("routes.twofa.hashlib.sha256") as mock_hash:
        mock_hash.return_value.hexdigest.return_value = email_hash
        response = client.post("/2fa-verify", json={"email": "test@e.ntu.edu.sg", "otp": "000000"})
        assert response.status_code == 401
        assert "Invalid OTP" in response.get_json()["error"]
