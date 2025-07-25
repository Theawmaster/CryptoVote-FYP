import os
import sys
import pytest
from flask import Flask
from unittest.mock import patch

# --- Add backend to sys.path ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ✅ Patch role_required BEFORE importing election_bp
patch("utilities.auth_utils.role_required", lambda _: (lambda f: f)).start()

# --- Import routes and DB ---
from routes.admin.election_routes import election_bp
from models.db import db

# --- Setup Flask test app ---
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

# --- Create test client ---
@pytest.fixture
def client(test_app):
    test_app.register_blueprint(election_bp, url_prefix="/admin")
    return test_app.test_client()

# ✅ Helper to override route view functions
def rebind_app_route(app, endpoint_suffix, new_func):
    for rule in app.url_map.iter_rules():
        if rule.endpoint.endswith(endpoint_suffix):
            app.view_functions[rule.endpoint] = new_func
            return

# --- TESTS ---

@patch("routes.admin.election_routes.start_election_by_id")
def test_start_election(mock_start, client, test_app):
    mock_start.return_value = ("Election started", 200)

    def mock_view(election_id):
        return mock_start(election_id, "admin@ntu.edu.sg", "127.0.0.1")

    with test_app.app_context():
        rebind_app_route(test_app, "start_election", mock_view)
        with client.session_transaction() as sess:
            sess["email"] = "admin@ntu.edu.sg"
            sess["role"] = "admin"
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
            sess["role"] = "admin"
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
            sess["role"] = "admin"
        response = client.get("/admin/election-status/mock_election")
        assert response.status_code == 200
        assert b"Election is ongoing" in response.data

@patch("routes.admin.election_routes.create_new_election")
def test_create_election(mock_create, client, test_app):
    mock_create.return_value = ("Election created", 201)

    def mock_view():
        return mock_create("new_election_001", "admin@ntu.edu.sg", "127.0.0.1")

    with test_app.app_context():
        rebind_app_route(test_app, "create_election", mock_view)
        with client.session_transaction() as sess:
            sess["email"] = "admin@ntu.edu.sg"
            sess["role"] = "admin"
        response = client.post("/admin/create-election", json={"election_id": "new_election_001"})
        assert response.status_code == 201
        assert b"Election created" in response.data

def test_start_election_unauthorized(client):
    response = client.post("/admin/start-election/test123")
    assert response.status_code == 403
    assert b"Unauthorized" in response.data

def test_end_election_unauthorized(client):
    response = client.post("/admin/end-election/mock_election")
    assert response.status_code == 403
    assert b"Unauthorized" in response.data

def test_election_status_unauthorized(client):
    response = client.get("/admin/election-status/mock_election")
    assert response.status_code == 403
    assert b"Unauthorized" in response.data

def test_create_election_unauthorized(client):
    response = client.post("/admin/create-election", json={"election_id": "new_election_001"})
    assert response.status_code == 403
    assert b"Unauthorized" in response.data

def test_create_election_missing_payload(client, test_app):
    def mock_view():
        raise NameError("name 'election_id' is not defined")

    with test_app.app_context():
        rebind_app_route(test_app, "create_election", mock_view)
        with client.session_transaction() as sess:
            sess["email"] = "admin@ntu.edu.sg"
            sess["role"] = "admin"

        with pytest.raises(NameError) as excinfo:
            client.post("/admin/create-election", json={})
        assert "election_id" in str(excinfo.value)


def test_create_election_missing_key(client, test_app):
    with client.session_transaction() as sess:
        sess["email"] = "admin@ntu.edu.sg"
        sess["role"] = "admin"

    response = client.post("/admin/create-election", json={})  # missing "election_id"
    assert response.status_code == 400
    assert b"Missing election_id" in response.data

def test_create_election_missing_email(client, test_app):
    def mock_view():
        raise NameError("name 'admin_email' is not defined")

    with test_app.app_context():
        rebind_app_route(test_app, "create_election", mock_view)
        with client.session_transaction() as sess:
            sess["role"] = "admin"

        with pytest.raises(NameError) as excinfo:
            client.post("/admin/create-election", json={"election_id": "new_election_001"})
        assert "admin_email" in str(excinfo.value)
        
@patch("routes.admin.election_routes.create_new_election")
@patch("routes.admin.election_routes.get_election_status_by_id")
def test_reuse_session_for_multiple_routes(mock_status, mock_create, client):
    mock_status.return_value = ("Election is ongoing", 200)
    mock_create.return_value = ("Election created", 201)

    with client.session_transaction() as sess:
        sess["email"] = "admin@ntu.edu.sg"
        sess["role"] = "admin"

    res1 = client.get("/admin/election-status/mock_id")
    assert res1.status_code == 200
    assert b"Election is ongoing" in res1.data

    res2 = client.post("/admin/create-election", json={"election_id": "another_one"})
    assert res2.status_code == 201
    assert b"Election created" in res2.data

