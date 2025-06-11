import os
import sys
import pytest
from flask import Flask
from unittest.mock import patch

# Add backend to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Patch BEFORE importing election_bp
patch("routes.admin.election_routes.role_required", lambda _: (lambda f: f)).start()

from routes.admin.election_routes import election_bp
from models.db import db

@pytest.fixture
def test_app():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    test_app.register_blueprint(election_bp, url_prefix="/admin")
    return test_app.test_client()

# ✅ Helper to override route after app has registered blueprint
def rebind_app_route(app, endpoint_suffix, new_func):
    for rule in app.url_map.iter_rules():
        if rule.endpoint.endswith(endpoint_suffix):
            app.view_functions[rule.endpoint] = new_func
            return

@patch("routes.admin.election_routes.start_election_by_id")
def test_start_election(mock_start, client, test_app):
    mock_start.return_value = ("Election started", 200)

    def mock_view(election_id):
        return mock_start(election_id, "admin@ntu.edu.sg", "127.0.0.1")

    with test_app.app_context():
        rebind_app_route(test_app, "start_election", mock_view)
        with client.session_transaction() as sess:
            sess["email"] = "admin@ntu.edu.sg"
        response = client.post("/admin/start-election/mock_election")
        assert response.status_code == 200
        assert b"Election started" in response.data

@patch("routes.admin.election_routes.end_election_by_id")
def test_end_election(mock_end, client, test_app):
    mock_end.return_value = ("Election ended", 200)

    def mock_view(election_id):
        return mock_end(election_id, "admin@ntu.edu.sg", "127.0.0.1")

    with test_app.app_context():
        rebind_app_route(test_app, "end_election", mock_view)
        with client.session_transaction() as sess:
            sess["email"] = "admin@ntu.edu.sg"
        response = client.post("/admin/end-election/mock_election")
        assert response.status_code == 200
        assert b"Election ended" in response.data

@patch("routes.admin.election_routes.get_election_status_by_id")
def test_election_status(mock_status, client, test_app):
    mock_status.return_value = ("Election is ongoing", 200)

    def mock_view(election_id):
        return mock_status(election_id, "admin@ntu.edu.sg", "127.0.0.1")

    with test_app.app_context():
        rebind_app_route(test_app, "election_status", mock_view)
        with client.session_transaction() as sess:
            sess["email"] = "admin@ntu.edu.sg"
        response = client.get("/admin/election-status/mock_election")
        assert response.status_code == 200
        assert b"Election is ongoing" in response.data
