import pytest
from flask import Flask, session, jsonify
from unittest.mock import patch, MagicMock

from cryptovote.backend.utilities.auth_utils import role_required

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test"
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_role_required_no_email(app, client):
    @app.route("/protected")
    @role_required("admin")
    def protected():
        return jsonify({"msg": "ok"})

    with client.session_transaction() as sess:
        sess.clear()  # No email in session

    response = client.get("/protected")
    assert response.status_code == 401
    assert b"Authentication required" in response.data

@patch("cryptovote.backend.utilities.auth_utils.db")
def test_role_required_voter_not_found(mock_db, app, client):
    mock_db.session.query.return_value.filter_by.return_value.first.return_value = None

    @app.route("/protected")
    @role_required("admin")
    def protected():
        return jsonify({"msg": "ok"})

    with client.session_transaction() as sess:
        sess["email"] = "nonexistent@example.com"
        sess["role"] = "admin"

    response = client.get("/protected")
    assert response.status_code == 403
    assert b"Admin role required" in response.data

@patch("cryptovote.backend.utilities.auth_utils.db")
def test_role_required_wrong_db_role(mock_db, app, client):
    voter_mock = MagicMock()
    voter_mock.vote_role = "voter"
    mock_db.session.query.return_value.filter_by.return_value.first.return_value = voter_mock

    @app.route("/protected")
    @role_required("admin")
    def protected():
        return jsonify({"msg": "ok"})

    with client.session_transaction() as sess:
        sess["email"] = "admin@example.com"
        sess["role"] = "admin"

    response = client.get("/protected")
    assert response.status_code == 403
    assert b"Admin role required" in response.data

@patch("cryptovote.backend.utilities.auth_utils.db")
def test_role_required_session_role_mismatch(mock_db, app, client):
    voter_mock = MagicMock()
    voter_mock.vote_role = "admin"
    mock_db.session.query.return_value.filter_by.return_value.first.return_value = voter_mock

    @app.route("/protected")
    @role_required("admin")
    def protected():
        return jsonify({"msg": "ok"})

    with client.session_transaction() as sess:
        sess["email"] = "admin@example.com"
        sess["role"] = "voter"  # Session role mismatch

    response = client.get("/protected")
    assert response.status_code == 403
    assert b"Unauthorized access" in response.data

@patch("cryptovote.backend.utilities.auth_utils.db")
def test_role_required_success(mock_db, app, client):
    voter_mock = MagicMock()
    voter_mock.vote_role = "admin"
    mock_db.session.query.return_value.filter_by.return_value.first.return_value = voter_mock

    @app.route("/protected")
    @role_required("admin")
    def protected():
        return jsonify({"msg": "ok"})

    with client.session_transaction() as sess:
        sess["email"] = "admin@example.com"
        sess["role"] = "admin"

    response = client.get("/protected")
    assert response.status_code == 200
    assert b"ok" in response.data
