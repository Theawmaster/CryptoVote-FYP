import os
import sys
import pytest
from flask import Flask
from unittest.mock import patch, MagicMock

# Dynamically add backend to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from routes.logout import logout_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(logout_bp, url_prefix="/logout")
    app.config['TESTING'] = True
    return app.test_client()

def test_logout_missing_email(client):
    response = client.post("/logout/", json={})
    assert response.status_code == 400
    assert "Email is required" in response.get_json()["error"]

@patch("routes.logout.Voter")
def test_logout_user_not_found(mock_voter_class, client):
    mock_voter_class.query.filter_by.return_value.first.return_value = None
    response = client.post("/logout/", json={"email": "ghost@e.ntu.edu.sg"})
    assert response.status_code == 404
    assert "User not found" in response.get_json()["error"]

@patch("routes.logout.Voter")
def test_logout_already_logged_out(mock_voter_class, client):
    mock_voter = MagicMock(logged_in=False)
    mock_voter_class.query.filter_by.return_value.first.return_value = mock_voter
    response = client.post("/logout/", json={"email": "ghost@e.ntu.edu.sg"})
    assert response.status_code == 200
    assert "already logged out" in response.get_json()["message"]

@patch("routes.logout.db")
@patch("routes.logout.Voter")
def test_logout_success(mock_voter_class, mock_db, client):
    mock_voter = MagicMock(logged_in=True)
    mock_voter_class.query.filter_by.return_value.first.return_value = mock_voter
    response = client.post("/logout/", json={"email": "valid@e.ntu.edu.sg"})
    assert response.status_code == 200
    assert "Logout successful" in response.get_json()["message"]

@patch("routes.logout.db")
@patch("routes.logout.Voter")
def test_logout_db_failure(mock_voter_class, mock_db, client):
    mock_voter = MagicMock(logged_in=True)
    mock_db.session.commit.side_effect = Exception("DB error")
    mock_voter_class.query.filter_by.return_value.first.return_value = mock_voter
    response = client.post("/logout/", json={"email": "valid@e.ntu.edu.sg"})
    assert response.status_code == 500
    assert "Logout failed" in response.get_json()["error"]
