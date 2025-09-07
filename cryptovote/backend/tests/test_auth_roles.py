# backend/tests/test_auth_roles.py
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
from flask import Flask

# Ensure backend/ on path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import routes.cast_vote as cv  # reuse the cast-vote blueprint from your app
from models.db import db

# --- voter endpoint tests reuse the shared 'app' & 'client' fixtures from tests/conftest.py ---
#     (that fixture already registers cv.cast_vote_bp and stubs db, etc.)

def _login(client):
    with client.session_transaction() as s:
        s["email"] = "unit@test"

def test_cast_vote_requires_session_email(client):
    """
    Unauthenticated voters cannot hit /cast-vote.
    Expect 401.
    """
    r = client.post("/cast-vote", json={})
    assert r.status_code == 401

def test_cast_vote_requires_verified(monkeypatch, client):
    """
    Voter must be verified; otherwise 403.
    """
    class _VoterQ:
        def filter_by(self, **kw): return self
        def first(self): return NS(id=1, is_verified=False, logged_in=True)
    monkeypatch.setattr(cv, "Voter", NS(query=_VoterQ()))

    _login(client)
    r = client.post("/cast-vote", json={"election_id":"E","token":"t","signature":"s"})
    assert r.status_code == 403

def test_cast_vote_requires_logged_in(monkeypatch, client):
    """
    Voter must be currently logged_in; otherwise 403.
    """
    class _VoterQ:
        def filter_by(self, **kw): return self
        def first(self): return NS(id=1, is_verified=True, logged_in=False)
    monkeypatch.setattr(cv, "Voter", NS(query=_VoterQ()))

    _login(client)
    r = client.post("/cast-vote", json={"election_id":"E","token":"t","signature":"s"})
    assert r.status_code == 403


# ---------- Admin role tests (skip gracefully if you don’t expose admin blueprints) ----------

def _import_admin_blueprint_or_skip():
    """
    Try to import routes.admin.election_routes and extract any Flask Blueprint(s).
    If not present, skip admin tests cleanly.
    """
    import importlib
    try:
        mod = importlib.import_module("routes.admin.election_routes")
    except Exception:
        pytest.skip("No admin routes module found (routes/admin/election_routes.py)")
    from flask import Blueprint
    bps = [v for v in vars(mod).values() if isinstance(v, Blueprint)]
    if not bps:
        pytest.skip("Admin module has no Blueprint objects")
    return bps

@pytest.fixture
def admin_app():
    from flask import Flask
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    # register all admin blueprints we can discover
    for bp in _import_admin_blueprint_or_skip():
        app.register_blueprint(bp)
    return app

@pytest.fixture
def admin_client(admin_app):
    return admin_app.test_client()

def _pick_admin_get_path_or_skip(app: Flask):
    """
    From app.url_map, pick a GET-able /admin* route without path params.
    If none, skip gracefully.
    """
    candidates = []
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and "<" not in rule.rule and rule.rule.startswith("/admin"):
            candidates.append(rule.rule)
    if not candidates:
        pytest.skip("No simple GET /admin* route to exercise (ok to skip)")
    return sorted(candidates)[0]

def test_admin_requires_auth(admin_app, admin_client):
    path = _pick_admin_get_path_or_skip(admin_app)

    # Unauthenticated -> 401 or 403 both acceptable depending on your guard
    r = admin_client.get(path)
    assert r.status_code in (401, 403)

def test_admin_requires_admin_role(admin_app, admin_client):
    path = _pick_admin_get_path_or_skip(admin_app)

    # Logged in but not admin -> expect 403
    with admin_client.session_transaction() as s:
        s["email"] = "unit@test"
        s["role"] = "voter"
    r = admin_client.get(path)
    assert r.status_code == 403

    # Admin -> should NOT be 401/403 (route may 200/302/400 depending on implementation)
    with admin_client.session_transaction() as s:
        s["email"] = "admin@test"
        s["role"] = "admin"
    r = admin_client.get(path)
    assert r.status_code not in (401, 403)
