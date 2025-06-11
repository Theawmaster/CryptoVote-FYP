import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
from services import report_service

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    with app.app_context():
        yield app

# Shared mock ZKP data
MOCK_ZKP = [{
    "candidate_id": "alice",
    "vote_count": 5,
    "salt": "abc123",
    "commitment": "commitXYZ"
}]

# ---------------- TEST CSV GENERATION ----------------

@patch("services.report_service.send_file")
@patch("services.report_service.log_admin_action")
def test_generate_csv_report(mock_log, mock_send, app):
    response = report_service.generate_csv_report(
        election_id=1,
        tally=MOCK_ZKP,
        zkp_proofs=MOCK_ZKP,
        admin_email="admin@ntu.edu.sg",
        ip_addr="127.0.0.1"
    )

    assert mock_send.called
    assert mock_log.called
    args, kwargs = mock_send.call_args
    assert kwargs["mimetype"] == "text/csv"

# ---------------- TEST PDF GENERATION ----------------

@patch("services.report_service.send_file")
@patch("services.report_service.FPDF")
@patch("services.report_service.log_admin_action")
@patch("services.report_service.os.path.exists", return_value=False)
def test_generate_pdf_report(mock_exists, mock_log, mock_fpdf, mock_send, app):
    mock_pdf = MagicMock()
    mock_pdf.output.return_value = "fake-pdf"  # Raw bytes not needed since send_file is mocked
    mock_fpdf.return_value = mock_pdf

    response = report_service.generate_pdf_report(
        election_id=1,
        tally=MOCK_ZKP,
        zkp_proofs=MOCK_ZKP,
        admin_email="admin@ntu.edu.sg",
        ip_addr="127.0.0.1"
    )

    assert mock_pdf.add_page.called
    assert mock_log.called
    assert mock_send.called
    args, kwargs = mock_send.call_args
    assert kwargs["mimetype"] == "application/pdf"

# ---------------- TEST DISPATCH FUNCTION ----------------

@patch("services.report_service.db")
@patch("services.report_service.tally_votes", return_value=MOCK_ZKP)
@patch("services.report_service.generate_all_zkp_proofs", return_value=MOCK_ZKP)
@patch("services.report_service.generate_pdf_report", return_value="PDF_RESPONSE")
@patch("services.report_service.generate_csv_report", return_value="CSV_RESPONSE")
def test_generate_report_file_csv(mock_csv, mock_pdf, mock_zkp, mock_tally, mock_db, app):
    mock_election = MagicMock()
    mock_db.session.query().filter_by().first.return_value = mock_election

    response = report_service.generate_report_file(
        election_id=1,
        format_type="csv",
        admin_email="admin@ntu.edu.sg",
        ip_addr="127.0.0.1"
    )

    assert response == "CSV_RESPONSE"
    mock_csv.assert_called_once()
    mock_pdf.assert_not_called()

@patch("services.report_service.db")
@patch("services.report_service.tally_votes", return_value=MOCK_ZKP)
@patch("services.report_service.generate_all_zkp_proofs", return_value=MOCK_ZKP)
@patch("services.report_service.generate_pdf_report", return_value="PDF_RESPONSE")
@patch("services.report_service.generate_csv_report", return_value="CSV_RESPONSE")
def test_generate_report_file_pdf(mock_csv, mock_pdf, mock_zkp, mock_tally, mock_db, app):
    mock_election = MagicMock()
    mock_db.session.query().filter_by().first.return_value = mock_election

    response = report_service.generate_report_file(
        election_id=1,
        format_type="pdf",
        admin_email="admin@ntu.edu.sg",
        ip_addr="127.0.0.1"
    )

    assert response == "PDF_RESPONSE"
    mock_pdf.assert_called_once()
    mock_csv.assert_not_called()

@patch("services.report_service.db")
def test_generate_report_file_format_not_supported(mock_db, app):
    mock_election = MagicMock()
    mock_db.session.query().filter_by().first.return_value = mock_election

    response, status = report_service.generate_report_file(
        election_id=1,
        format_type="html",
        admin_email="admin@ntu.edu.sg",
        ip_addr="127.0.0.1"
    )

    assert status == 400
    assert "Unsupported format" in response.json["error"]

@patch("services.report_service.db")
def test_generate_report_file_election_not_found(mock_db, app):
    mock_db.session.query().filter_by().first.return_value = None

    response, status = report_service.generate_report_file(
        election_id=1,
        format_type="pdf",
        admin_email="admin@ntu.edu.sg",
        ip_addr="127.0.0.1"
    )

    assert status == 404
    assert "not found" in response.json["error"]
