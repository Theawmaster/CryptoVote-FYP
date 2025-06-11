import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify
from models.db import db  


# Add project root to sys.path dynamically
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import after path fix
from routes.cast_vote import cast_vote_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True

    # Initialize SQLAlchemy properly
    db.init_app(app)

    app.register_blueprint(cast_vote_bp)

    with app.app_context():
        db.create_all()
        yield app.test_client()

def test_missing_fields(client):
    response = client.post("/cast-vote", json={})
    assert response.status_code == 400
    assert "Missing field" in response.get_json()["error"]

@patch("routes.cast_vote.validate_vote_request")
def test_invalid_vote_request(mock_validate, client):
    with client.application.app_context():
        mock_validate.return_value = (
            False, jsonify({"error": "Missing field 'token'"}), 400
        )
        response = client.post("/cast-vote", json={"token": ""})
        assert response.status_code == 400
        assert "token" in response.get_json()["error"]

@patch("routes.cast_vote.load_rsa_pubkey")
@patch("routes.cast_vote.validate_vote_request", return_value=(True, None, None))
@patch("routes.cast_vote.parse_and_verify_signature")
def test_invalid_signature(mock_parse, mock_validate, mock_key, client):
    with client.application.app_context():
        mock_parse.return_value = (False, None, (jsonify({"error": "Invalid signature"}), 400))
        payload = {
            "token": "voteforA",
            "signature": "deadbeef",
            "candidate_id": "alice"
        }
        response = client.post("/cast-vote", json=payload)
        assert response.status_code == 400  # `jsonify` creates response with 200 unless overridden
        assert "signature" in response.get_json()["error"]

@patch("routes.cast_vote.load_rsa_pubkey")
@patch("routes.cast_vote.validate_vote_request", return_value=(True, None, None))
@patch("routes.cast_vote.parse_and_verify_signature", return_value=(True, 123456789, None))
@patch("routes.cast_vote.is_token_used", return_value=True)
def test_token_already_used(mock_used, mock_parse, mock_validate, mock_key, client):
    payload = {
        "token": "voteforA",
        "signature": "deadbeef",
        "candidate_id": "alice"
    }
    response = client.post("/cast-vote", json=payload)
    assert response.status_code == 403
    assert "already been used" in response.get_json()["error"]

@patch("routes.cast_vote.load_paillier_public_key")
@patch("routes.cast_vote.load_rsa_pubkey")
@patch("routes.cast_vote.validate_vote_request", return_value=(True, None, None))
@patch("routes.cast_vote.parse_and_verify_signature", return_value=(True, 123456789, None))
@patch("routes.cast_vote.is_token_used", return_value=False)
@patch("models.issued_token.IssuedToken.query")
@patch("models.db.db.session")
def test_successful_vote(mock_db, mock_query, mock_used, mock_parse, mock_validate, mock_key_rsa, mock_key_paillier, client):
    app = client.application
    with app.app_context():  # 🔥 this is the missing context
        # Mock Paillier encryption result
        mock_enc = MagicMock()
        mock_enc.ciphertext.return_value = 123456
        mock_enc.exponent = 65537
        mock_key_paillier.return_value.encrypt.return_value = mock_enc

        mock_token = MagicMock()
        mock_query.filter_by.return_value.first.return_value = mock_token

        payload = {
            "token": "voteforA",
            "signature": "deadbeef",
            "candidate_id": "alice"
        }

        response = client.post("/cast-vote", json=payload)
        assert response.status_code == 200
        assert "successfully" in response.get_json()["message"]
