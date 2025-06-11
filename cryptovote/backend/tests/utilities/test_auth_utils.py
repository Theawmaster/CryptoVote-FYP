import pytest
from flask import Flask, session, jsonify
from unittest.mock import patch, MagicMock
from utilities import auth_utils


app = Flask(__name__)
app.secret_key = "testing_secret"  # Needed for session


@app.route("/admin-only")
@auth_utils.role_required("admin")
def protected_view():
    return jsonify({"message": "Welcome, admin!"})

@patch("utilities.auth_utils.db")
@patch("utilities.auth_utils.Voter")
def test_no_session_redirect(mock_voter, mock_db):
    with app.test_request_context("/admin-only"):
        # Clear session
        session.clear()

        response = protected_view()
        assert response[1] == 401
        assert b"Authentication required" in response[0].data


@patch("utilities.auth_utils.db")
@patch("utilities.auth_utils.Voter")
def test_incorrect_role(mock_voter, mock_db):
    with app.test_request_context("/admin-only"):
        session["email"] = "test@example.com"
        session["role"] = "voter"

        fake_voter = MagicMock()
        fake_voter.vote_role = "voter"

        mock_db.session.query().filter_by().first.return_value = fake_voter

        response = protected_view()
        assert response[1] == 403
        assert b"Admin role required" in response[0].data


@patch("utilities.auth_utils.db")
@patch("utilities.auth_utils.Voter")
def test_correct_role_access(mock_voter, mock_db):
    with app.test_request_context("/admin-only"):
        session["email"] = "admin@example.com"
        session["role"] = "admin"

        fake_voter = MagicMock()
        fake_voter.vote_role = "admin"

        mock_db.session.query().filter_by().first.return_value = fake_voter

        response = protected_view()
        assert response.status_code == 200
        assert b"Welcome, admin!" in response.data
