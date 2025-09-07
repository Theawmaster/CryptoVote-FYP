# backend/tests/test_rsa_public_key_config.py
import sys
from pathlib import Path
import pytest
from flask import Flask

# Ensure "backend/" is importable
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import routes.public_keys as pk  # your module

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    # ✅ your blueprint is named keys_bp
    app.register_blueprint(pk.keys_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def _assert_e_is_65537(obj: dict):
    # accept either "eDec" or "e"
    e = str(obj.get("eDec") or obj.get("e") or "")
    if not e:
        pytest.skip("RSA served without exponent field")
    assert e == "65537", f"Unexpected RSA exponent: {e}"

def test_rsa_e_is_65537_if_present(client):
    # Prefer the dedicated endpoint if available
    r = client.get("/public-keys/rsa")
    if r.status_code == 200:
        j = r.get_json() or {}
        _assert_e_is_65537(j)
        return

    # Fallback to combined endpoint
    r = client.get("/public-keys")
    if r.status_code != 200:
        pytest.skip("No /public-keys route enabled")

    j = r.get_json() or {}
    rsa = j.get("rsa")

    if not rsa:
        pytest.skip("No RSA key exposed in /public-keys")

    # Your current implementation returns an object; handle both shapes
    if isinstance(rsa, dict):
        _assert_e_is_65537(rsa)
    elif isinstance(rsa, list) and rsa:
        _assert_e_is_65537(rsa[0])
    else:
        pytest.skip("RSA present but empty/unknown shape")
