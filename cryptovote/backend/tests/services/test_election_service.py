import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
from services import election_service

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    with app.app_context():
        yield app

def make_mock_election(started=False, ended=False):
    mock = MagicMock()
    mock.has_started = started
    mock.has_ended = ended
    mock.is_active = not ended
    mock.start_time = None
    mock.end_time = None
    return mock

# --- START ELECTION TESTS ---

@patch("services.election_service.db")
def test_start_election_not_found(mock_db, app):
    mock_db.session.query().filter_by().first.return_value = None
    response, status = election_service.start_election_by_id(1, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 404
    assert "not found" in response.json["error"]

@patch("services.election_service.db")
def test_start_election_already_started(mock_db, app):
    mock_election = make_mock_election(started=True)
    mock_db.session.query().filter_by().first.return_value = mock_election
    response, status = election_service.start_election_by_id(1, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 200
    assert "already started" in response.json["message"]

@patch("services.election_service.log_admin_action")
@patch("services.election_service.db")
def test_start_election_success(mock_db, mock_log, app):
    mock_election = make_mock_election(started=False)
    mock_db.session.query().filter_by().first.return_value = mock_election
    response, status = election_service.start_election_by_id(1, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 200
    assert response.json["message"].startswith("✅")
    assert mock_election.has_started is True
    assert mock_election.is_active is True

# --- END ELECTION TESTS ---

@patch("services.election_service.db")
def test_end_election_not_found(mock_db, app):
    mock_db.session.query().filter_by().first.return_value = None
    response, status = election_service.end_election_by_id(2, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 404
    assert "not found" in response.json["error"]

@patch("services.election_service.db")
def test_end_election_already_ended(mock_db, app):
    mock_election = make_mock_election(ended=True)
    mock_db.session.query().filter_by().first.return_value = mock_election
    response, status = election_service.end_election_by_id(2, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 200
    assert "already ended" in response.json["message"]

@patch("services.election_service.log_admin_action")
@patch("services.election_service.db")
def test_end_election_success(mock_db, mock_log, app):
    mock_election = make_mock_election(ended=False)
    mock_db.session.query().filter_by().first.return_value = mock_election
    response, status = election_service.end_election_by_id(2, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 200
    assert response.json["message"].startswith("🛑")
    assert mock_election.has_ended is True
    assert mock_election.is_active is False

# --- GET STATUS TESTS ---

@patch("services.election_service.db")
def test_get_election_status_not_found(mock_db, app):
    mock_db.session.query().filter_by().first.return_value = None
    response, status = election_service.get_election_status_by_id(3, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 404
    assert "not found" in response.json["error"]

@patch("services.election_service.log_admin_action")
@patch("services.election_service.db")
def test_get_election_status_success(mock_db, mock_log, app):
    mock_election = make_mock_election(started=True, ended=False)
    mock_election.start_time = "2025-06-10T12:00:00Z"
    mock_election.end_time = None
    mock_db.session.query().filter_by().first.return_value = mock_election

    response, status = election_service.get_election_status_by_id(3, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 200
    data = response.get_json()
    assert data["has_started"] is True
    assert data["has_ended"] is False
    assert data["is_active"] is True
    assert data["start_time"] == "2025-06-10T12:00:00Z"

# --- CREATE ELECTION TESTS ---

@patch("services.election_service.db")
def test_create_election_missing_field(mock_db, app):
    data = {"id": "E123"}  # Missing 'name'
    response, status = election_service.create_new_election(data, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 400
    assert "Missing required field" in response.json["error"]

@patch("services.election_service.db")
def test_create_election_duplicate_id(mock_db, app):
    mock_db.session.query().filter_by().first.return_value = MagicMock()  # Simulate existing election
    data = {"id": "E123", "name": "My Election"}
    response, status = election_service.create_new_election(data, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 400
    assert "already exists" in response.json["error"]

@patch("services.election_service.log_admin_action")
@patch("services.election_service.db")
def test_create_election_success(mock_db, mock_log, app):
    mock_db.session.query().filter_by().first.return_value = None  # No duplicate
    mock_db.session.add = MagicMock()
    mock_db.session.commit = MagicMock()

    data = {"id": "E123", "name": "My Election"}
    response, status = election_service.create_new_election(data, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 201
    assert response.json["message"].startswith("🆕")

@patch("services.election_service.db")
def test_start_election_db_failure(mock_db, app):
    mock_election = make_mock_election(started=False)
    mock_db.session.query().filter_by().first.return_value = mock_election
    mock_db.session.commit.side_effect = Exception("DB failure")

    response, status = election_service.start_election_by_id(4, "admin@ntu.edu.sg", "127.0.0.1")

    assert status == 500
    assert "DB failure" in response.json["error"]
    mock_db.session.rollback.assert_called_once()

@patch("services.election_service.db")
def test_end_election_db_failure(mock_db, app):
    mock_election = make_mock_election(ended=False)
    mock_db.session.query().filter_by().first.return_value = mock_election
    mock_db.session.commit.side_effect = Exception("DB crash")

    response, status = election_service.end_election_by_id(5, "admin@ntu.edu.sg", "127.0.0.1")

    assert status == 500
    assert "DB crash" in response.json["error"]
    mock_db.session.rollback.assert_called_once()

@patch("services.election_service.db")
def test_create_election_db_failure(mock_db, app):
    mock_db.session.query().filter_by().first.return_value = None
    mock_db.session.commit.side_effect = Exception("Insert failed")

    data = {"id": "E456", "name": "Fail Election"}
    response, status = election_service.create_new_election(data, "admin@ntu.edu.sg", "127.0.0.1")

    assert status == 500
    assert "Server error" in response.json["error"]
    mock_db.session.rollback.assert_called_once()
