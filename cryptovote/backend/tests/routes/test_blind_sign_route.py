import sys, os
import pytest
from flask import Flask
from unittest.mock import patch, MagicMock

# Dynamically add backend path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from routes.blind_sign import blind_sign_bp

@pytest.fixture
def client():
    from backend.app import db  # Import your shared SQLAlchemy instance
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)  # Bind SQLAlchemy instance to this Flask app

    with app.app_context():
        db.create_all()
        app.register_blueprint(blind_sign_bp)
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_missing_email_or_token(client):
    res = client.post("/blind-sign", json={})
    assert res.status_code == 400
    assert "error" in res.get_json()

@patch("routes.blind_sign.Voter")
@patch("cryptovote.backend.routes.blind_sign.hashlib.sha256")
def test_unauthorized_voter(mock_sha, mock_voter_class, client):
    mock_sha.return_value.hexdigest.return_value = "hash"
    mock_voter_class.query.filter_by.return_value.first.return_value = None
    res = client.post("/blind-sign", json={"email": "test@e.ntu.edu.sg", "blinded_token": "abc123"})
    assert res.status_code == 403

@patch("cryptovote.backend.routes.blind_sign.db")
@patch("cryptovote.backend.routes.blind_sign.IssuedToken")
@patch("cryptovote.backend.routes.blind_sign.sign_blinded_token", return_value=123456789)
@patch("routes.blind_sign.Voter")
def test_successful_token_signing(mock_voter_class, mock_sign, mock_token, mock_db, client):
    voter = MagicMock(is_verified=True, logged_in=True, has_token=False)
    mock_voter_class.query.filter_by.return_value.first.return_value = voter

    res = client.post("/blind-sign", json={"email": "test@e.ntu.edu.sg", "blinded_token": "abc"})
    assert res.status_code == 200
    assert "signed_blinded_token" in res.get_json()

@patch("routes.blind_sign.Voter")
def test_token_already_issued(mock_voter_class, client):
    voter = MagicMock(is_verified=True, logged_in=True, has_token=True)
    mock_voter_class.query.filter_by.return_value.first.return_value = voter

    res = client.post("/blind-sign", json={"email": "test@e.ntu.edu.sg", "blinded_token": "abc"})
    assert res.status_code == 403
    assert "already issued" in res.get_json()["error"]

def test_missing_fields(client):
    response = client.post("/blind-sign", json={})
    assert response.status_code == 400
    assert "required" in response.get_json()["error"]

@patch("routes.blind_sign.Voter")
@patch("cryptovote.backend.routes.blind_sign.hashlib.sha256")
def test_unauthorized_user(mock_hashlib, mock_voter_class, client):
    mock_hashlib.return_value.hexdigest.return_value = "dummyhash"
    mock_voter_class.query.filter_by.return_value.first.return_value = None
    response = client.post("/blind-sign", json={"email": "user@e.ntu.edu.sg", "blinded_token": "abc123"})
    assert response.status_code == 403
    assert "Unauthorized" in response.get_json()["error"]

@patch("routes.blind_sign.Voter")
@patch("cryptovote.backend.routes.blind_sign.hashlib.sha256")
def test_already_issued_token(mock_hashlib, mock_voter_class, client):
    mock_hashlib.return_value.hexdigest.return_value = "dummyhash"
    mock_voter = MagicMock(is_verified=True, logged_in=True, has_token=True)
    mock_voter_class.query.filter_by.return_value.first.return_value = mock_voter
    response = client.post("/blind-sign", json={"email": "user@e.ntu.edu.sg", "blinded_token": "abc123"})
    assert response.status_code == 403
    assert "Token already issued" in response.get_json()["error"]

@patch("cryptovote.backend.routes.blind_sign.db")
@patch("cryptovote.backend.routes.blind_sign.IssuedToken")
@patch("cryptovote.backend.routes.blind_sign.sign_blinded_token", return_value=1234567890)
@patch("routes.blind_sign.Voter")
@patch("cryptovote.backend.routes.blind_sign.hashlib.sha256")
def test_successful_blind_sign(
    mock_hashlib, mock_voter_class, mock_sign, mock_issued_token_class, mock_db, client
):
    mock_hash = MagicMock()
    mock_hash.hexdigest.return_value = "tokenhash"
    mock_hashlib.return_value = mock_hash

    mock_voter = MagicMock(is_verified=True, logged_in=True, has_token=False)
    mock_voter_class.query.filter_by.return_value.first.return_value = mock_voter

    response = client.post("/blind-sign", json={
        "email": "user@e.ntu.edu.sg",
        "blinded_token": "1a2b3c"
    })
    assert response.status_code == 200
    assert "signed_blinded_token" in response.get_json()