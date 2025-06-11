import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask

# Set up path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# PATCH BEFORE importing audit_routes
with patch("utilities.auth_utils.role_required", lambda role: (lambda f: f)):
    from routes.admin.audit_routes import audit_bp
    from models.db import db  # Shared db instance

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(audit_bp, url_prefix="/admin")

    with app.app_context():
        db.create_all()
        with app.test_client() as client:
            yield client

@patch("routes.admin.audit_routes.perform_audit_report")
def test_audit_report_success(mock_audit, client):
    mock_audit.return_value = ("Audit completed", 200)
    with client.session_transaction() as sess:
        sess["email"] = "admin@e.ntu.edu.sg"

    response = client.get("/admin/audit-report/test_election")
    assert response.status_code == 200
    assert "Audit completed" in response.get_data(as_text=True)

@patch("routes.admin.audit_routes.perform_tally")
def test_tally_election_success(mock_tally, client):
    mock_tally.return_value = ("Tally successful", 200)
    with client.session_transaction() as sess:
        sess["email"] = "admin@e.ntu.edu.sg"

    response = client.post("/admin/tally-election/test_election")
    assert response.status_code == 200
    assert "Tally successful" in response.get_data(as_text=True)
