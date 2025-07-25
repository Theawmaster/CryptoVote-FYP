import sys, os
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask

# 👇 Dynamically add cryptovote/backend to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 👇 Import after sys.path is updated to mimic runtime from app.py
from routes.auth import auth_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(auth_bp)
    app.config['TESTING'] = True
    return app.test_client()

def test_login_missing_email(client):
    response = client.post("/login", json={})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Email is required"

@patch("routes.auth.Voter")
@patch("routes.auth.get_email_hash", return_value="mocked_hash")
def test_login_unverified_user(mock_hash, mock_voter_class, client):
    mock_voter_class.query.filter_by.return_value.first.return_value = MagicMock(is_verified=False)
    response = client.post("/login", json={"email": "user@e.ntu.edu.sg"})
    assert response.status_code == 403
    assert "Unverified" in response.get_json()["error"]

@patch("routes.auth.Voter")
@patch("routes.auth.get_email_hash", return_value="mocked_hash")
@patch("routes.auth.request_nonce", return_value="mocked_nonce")
def test_login_request_nonce_if_not_logged_in(mock_nonce, mock_hash, mock_voter_class, client):
    mock_voter = MagicMock(is_verified=True, logged_in=False)
    mock_voter_class.query.filter_by.return_value.first.return_value = mock_voter
    response = client.post("/login", json={"email": "user@e.ntu.edu.sg"})
    assert response.status_code == 200
    assert response.get_json()["nonce"] == "mocked_nonce"

@patch("routes.auth.Voter")
@patch("routes.auth.get_email_hash", return_value="mocked_hash")
def test_login_already_logged_in(mock_hash, mock_voter_class, client):
    mock_voter = MagicMock(is_verified=True, logged_in=True)
    mock_voter_class.query.filter_by.return_value.first.return_value = mock_voter
    response = client.post("/login", json={"email": "user@e.ntu.edu.sg"})
    assert response.status_code == 200
    assert "already signed in" in response.get_json()["message"]

@patch("routes.auth.db")
@patch("routes.auth.clear_nonce")
@patch("routes.auth.verify_voter_signature", return_value=(True, "OK"))
@patch("routes.auth.validate_nonce", return_value=("valid_nonce", None))
@patch("routes.auth.get_email_hash", return_value="mocked_hash")
@patch("routes.auth.Voter")
def test_login_signature_success(mock_voter_class, mock_hash, mock_validate, mock_verify, mock_clear, mock_db, client):
    voter_mock = MagicMock(is_verified=True, logged_in=False)
    mock_voter_class.query.filter_by.return_value.first.return_value = voter_mock
    response = client.post("/login", json={
        "email": "user@e.ntu.edu.sg",
        "signed_nonce": "signed123"
    })
    assert response.status_code == 200
    assert "Login successful" in response.get_json()["message"]

@patch("routes.auth.db")
@patch("routes.auth.failed_logins_last_10min", return_value=0)  # 👈 Add this
@patch("routes.auth.verify_voter_signature", return_value=(False, "Bad signature"))
@patch("routes.auth.validate_nonce", return_value=("valid_nonce", None))
@patch("routes.auth.get_email_hash", return_value="mocked_hash")
@patch("routes.auth.Voter")
def test_login_signature_failure(
    mock_voter_class, mock_hash, mock_validate, mock_verify, mock_failed_logins, mock_db, client
):
    mock_voter = MagicMock(is_verified=True, logged_in=False)
    mock_voter_class.query.filter_by.return_value.first.return_value = mock_voter
    response = client.post("/login", json={
        "email": "user@e.ntu.edu.sg",
        "signed_nonce": "bad_signature"
    })
    assert response.status_code == 401
    assert "signature" in response.get_json()["error"].lower()

@patch("routes.auth.validate_nonce", return_value=(None, "Nonce expired"))
@patch("routes.auth.get_email_hash", return_value="mocked_hash")
@patch("routes.auth.Voter")
def test_login_expired_nonce(mock_voter_class, mock_hash, mock_validate, client):
    mock_voter = MagicMock(is_verified=True, logged_in=False)
    mock_voter_class.query.filter_by.return_value.first.return_value = mock_voter
    response = client.post("/login", json={
        "email": "user@e.ntu.edu.sg",
        "signed_nonce": "signed123"
    })
    assert response.status_code == 403
    assert "expired" in response.get_json()["error"].lower()

@patch("routes.auth.db")
@patch("routes.auth.clear_nonce")
@patch("routes.auth.verify_voter_signature", return_value=(True, "OK"))
@patch("routes.auth.validate_nonce", return_value=("valid_nonce", None))
@patch("routes.auth.get_email_hash", return_value="mocked_hash")
@patch("routes.auth.Voter")
def test_login_signature_verified_but_db_commit_fails(mock_voter_class, mock_hash, mock_validate, mock_verify, mock_clear, mock_db, client):
    voter_mock = MagicMock(is_verified=True, logged_in=False)
    mock_voter_class.query.filter_by.return_value.first.return_value = voter_mock
    mock_db.session.commit.side_effect = Exception("Commit failed")

    response = client.post("/login", json={
        "email": "user@e.ntu.edu.sg",
        "signed_nonce": "signed123"
    })

    assert response.status_code == 500
    assert "failed to update" in response.get_json()["error"]
    mock_db.session.rollback.assert_called_once()

@patch("routes.auth.db")
@patch("routes.auth.failed_logins_last_10min", return_value=4)
@patch("routes.auth.flag_suspicious_activity")
@patch("routes.auth.verify_voter_signature", return_value=(False, "Bad signature"))
@patch("routes.auth.validate_nonce", return_value=("valid_nonce", None))
@patch("routes.auth.get_email_hash", return_value="mocked_hash")
@patch("routes.auth.Voter")
def test_login_signature_failure_multiple_failed_logins(
    mock_voter_class, mock_hash, mock_validate, mock_verify,
    mock_flag, mock_failed_logins, mock_db, client
):
    voter_mock = MagicMock(is_verified=True, logged_in=False)
    mock_voter_class.query.filter_by.return_value.first.return_value = voter_mock

    response = client.post("/login", json={
        "email": "user@e.ntu.edu.sg",
        "signed_nonce": "invalid"
    })

    assert response.status_code == 401
    assert "bad signature" in response.get_json()["error"].lower()
    assert mock_flag.call_count == 2  # Both flags triggered

def test_dev_login_admin_missing_email_hash(client):
    response = client.get("/admin/dev-login-admin")
    assert response.status_code == 400
    assert "Missing email_hash" in response.get_json()["error"]

@patch("routes.auth.Voter")
def test_dev_login_admin_voter_not_found(mock_voter_class, client):
    mock_voter_class.query.filter_by.return_value.first.return_value = None
    response = client.get("/admin/dev-login-admin?email_hash=fakehash")
    assert response.status_code == 404
    assert "No voter found" in response.get_json()["error"]

@patch("routes.auth.Voter")
def test_dev_login_admin_not_admin(mock_voter_class, client):
    voter = MagicMock(vote_role="voter")
    mock_voter_class.query.filter_by.return_value.first.return_value = voter
    response = client.get("/admin/dev-login-admin?email_hash=fakehash")
    assert response.status_code == 403
    assert "not an admin" in response.get_json()["error"]

@patch("routes.auth.Voter")
def test_dev_login_admin_exception(mock_voter_class, client):
    mock_voter_class.query.filter_by.side_effect = Exception("DB error")
    response = client.get("/admin/dev-login-admin?email_hash=fakehash")
    assert response.status_code == 500
    assert "internal server error" in response.get_json()["error"].lower()
