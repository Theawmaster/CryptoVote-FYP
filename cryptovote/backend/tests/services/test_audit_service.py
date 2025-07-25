import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
from services import audit_service


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    with app.app_context():
        yield app


def make_mock_election(has_ended=True, tally_generated=False):
    mock_election = MagicMock()
    mock_election.has_ended = has_ended
    mock_election.tally_generated = tally_generated
    return mock_election


@patch("services.audit_service.db")
def test_perform_tally_election_not_found(mock_db, app):
    mock_db.session.query().filter_by().first.return_value = None
    response, status = audit_service.perform_tally(1, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 404
    assert response.json["error"] == "Election not found"


@patch("services.audit_service.db")
def test_perform_tally_election_not_ended(mock_db, app):
    mock_db.session.query().filter_by().first.return_value = make_mock_election(has_ended=False)
    response, status = audit_service.perform_tally(1, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 400
    assert "before election ends" in response.json["error"]


@patch("services.audit_service.db")
def test_perform_tally_already_done(mock_db, app):
    mock_db.session.query().filter_by().first.return_value = make_mock_election(tally_generated=True)
    response, status = audit_service.perform_tally(1, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 400
    assert "already generated" in response.json["error"]


@patch("services.audit_service.log_admin_action")
@patch("services.audit_service.generate_all_zkp_proofs", return_value=["proof1", "proof2"])
@patch("services.audit_service.tally_votes", return_value={"alice": 3, "bob": 5})
@patch("services.audit_service.db")
def test_perform_tally_success(mock_db, mock_tally, mock_zkp, mock_log, app):
    mock_election = make_mock_election()
    mock_db.session.query().filter_by().first.return_value = mock_election
    response, status = audit_service.perform_tally(1, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 200
    assert response.json["tally"] == {"alice": 3, "bob": 5}
    assert response.json["zkp_proofs"] == ["proof1", "proof2"]
    assert response.json["message"].startswith("✅")


@patch("services.audit_service.db")
def test_perform_audit_report_election_not_found(mock_db, app):
    mock_db.session.query().filter_by().first.return_value = None
    response, status = audit_service.perform_audit_report(1, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 404
    assert response.json["error"] == "Election not found"


@patch("services.audit_service.log_admin_action")
@patch("services.audit_service.generate_all_zkp_proofs", return_value=["proofA", "proofB"])
@patch("services.audit_service.tally_votes", return_value={"carol": 7, "dave": 2})
@patch("services.audit_service.db")
def test_perform_audit_report_success(mock_db, mock_tally, mock_zkp, mock_log, app):
    mock_election = make_mock_election()
    mock_db.session.query().filter_by().first.return_value = mock_election
    response = audit_service.perform_audit_report(1, "admin@ntu.edu.sg", "127.0.0.1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["election_id"] == 1
    assert data["tally"] == {"carol": 7, "dave": 2}
    assert data["zkp_proofs"] == ["proofA", "proofB"]
    assert data["verifier_link"] == "/admin/verify-proof"

@patch("services.audit_service.generate_all_zkp_proofs", side_effect=Exception("ZKP boom"))
@patch("services.audit_service.tally_votes", return_value={"a": 1})
@patch("services.audit_service.db")
def test_perform_tally_internal_error(mock_db, mock_tally, mock_zkp, app):
    mock_db.session.query().filter_by().first.return_value = make_mock_election()
    response, status = audit_service.perform_tally(1, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 500
    assert "ZKP boom" in response.json["error"]

@patch("services.audit_service.log_admin_action", side_effect=Exception("Log error"))
@patch("services.audit_service.generate_all_zkp_proofs", return_value=["proofZ"])
@patch("services.audit_service.tally_votes", return_value={"eve": 4})
@patch("services.audit_service.db")
def test_perform_audit_report_logging_failure(mock_db, mock_tally, mock_zkp, mock_log, app):
    mock_db.session.query().filter_by().first.return_value = make_mock_election()
    response = audit_service.perform_audit_report(2, "admin@ntu.edu.sg", "127.0.0.1")
    assert response.status_code == 200
    assert response.get_json()["election_id"] == 2

@patch("services.audit_service.log_admin_action", side_effect=Exception("Log fail"))
@patch("services.audit_service.generate_all_zkp_proofs", return_value=["proofX"])
@patch("services.audit_service.tally_votes", return_value={"zoe": 8})
@patch("services.audit_service.db")
def test_perform_tally_logging_failure(mock_db, mock_tally, mock_zkp, mock_log, app):
    mock_election = make_mock_election()
    mock_db.session.query().filter_by().first.return_value = mock_election
    response, status = audit_service.perform_tally(3, "admin@ntu.edu.sg", "127.0.0.1")
    assert status == 200
    assert response.json["tally"] == {"zoe": 8}
