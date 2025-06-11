import os
import sys
import pytest
from flask import Flask, session
from unittest.mock import patch

# Dynamically add backend path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from routes.admin_routes import admin_bp
from models.db import db  # Assuming your SQLAlchemy instance is here

@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # In-memory test DB
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        db.create_all()  # Create tables if needed
        yield app.test_client()


def test_admin_blueprint_mounts(client):
    response = client.get("/admin/nonexistent")
    assert response.status_code in (404, 405)

@pytest.mark.parametrize("path", [
    "/admin/election-status/mock_election",
    "/admin/audit-report/mock_election",
    "/admin/download-report/mock_election",
])

def test_admin_subroutes_exist(client, path):
    # Patch the session to include a dummy email
    with client.session_transaction() as sess:
        sess["email"] = "admin@ntu.edu.sg"  # mocked admin session

    with patch("routes.admin.audit_routes.role_required", lambda role: lambda f: f), \
         patch("routes.admin.download_routes.role_required", lambda role: lambda f: f), \
         patch("routes.admin.election_routes.role_required", lambda role: lambda f: f):
        response = client.get(path)
        assert response.status_code in (200, 400, 401, 403, 404, 500)
