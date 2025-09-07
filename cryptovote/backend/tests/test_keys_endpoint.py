# backend/tests/test_keys_endpoint.py
import os
import sys
from pathlib import Path
import pytest
from flask import Flask

# Ensure backend/ is importable
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import routes.public_keys as pk  # adjust if yours lives elsewhere

try:
    from phe import paillier
except Exception:
    paillier = None


@pytest.fixture
def app(monkeypatch):
    assert paillier is not None, "phe/paillier not installed for tests"

    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret")

    # Fast test key; production min enforced in a separate test via env flag.
    pub, _ = paillier.generate_paillier_keypair(n_length=256)

    # --- Find & patch the loader symbol the endpoint uses ---
    patched = False

    # 1) Common names on the same module
    for attr in ("load_paillier_public_key", "load_public_key"):
        if hasattr(pk, attr):
            monkeypatch.setattr(pk, attr, lambda: pub)
            patched = True
            break

    # 2) Indirect import via utilities.paillier_utils
    if not patched:
        try:
            import utilities.paillier_utils as pau  # type: ignore
            if hasattr(pau, "load_public_key"):
                monkeypatch.setattr(pau, "load_public_key", lambda: pub)
                patched = True
        except Exception:
            pass

    if not patched:
        pytest.skip("Could not locate a load_public_key function to patch for paillier")

    # --- Register the blueprint (name may vary slightly) ---
    bp = getattr(pk, "public_keys_bp", None) or getattr(pk, "keys_bp", None)
    if not bp:
        pytest.skip("public_keys blueprint not found on routes.public_keys")
    app.register_blueprint(bp)

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _get_paillier(client):
    """Try a few likely paths and return (status_code, json) if found."""
    for path in ("/public-keys/paillier", "/public-keys/paillier/", "/public-keys"):
        r = client.get(path)
        if r.status_code == 200:
            try:
                j = r.get_json()
            except Exception:
                j = None
            if isinstance(j, dict):
                # If /public-keys returns a bundle, try "paillier" sub-object
                if "nHex" in j or "n_hex" in j or "key_id" in j:
                    return r.status_code, j
                if "paillier" in j and isinstance(j["paillier"], dict):
                    return r.status_code, j["paillier"]
    return None, None


def test_paillier_endpoint_shape_and_bits(client):
    """✅ Shape & internal consistency; dev key can be small for speed."""
    code, j = _get_paillier(client)
    assert code == 200 and isinstance(j, dict), "Paillier endpoint not reachable/JSON"

    assert "key_id" in j and isinstance(j["key_id"], str)
    assert j["key_id"].startswith("paillier-")

    # Allow nHex or n_hex
    n_hex = j.get("nHex") or j.get("n_hex")
    assert isinstance(n_hex, str) and len(n_hex) > 0, "n hex missing"
    n = int(n_hex, 16)

    # bits either provided or computable
    bits_reported = j.get("bits")
    if bits_reported is not None:
        assert isinstance(bits_reported, int)
        assert bits_reported == n.bit_length()
    else:
        # Accept no 'bits' field but ensure sanity
        assert n.bit_length() >= 128  # unit-test minimum (fast)

def test_paillier_key_id_is_consistent(client):
    """Key ID should be a deterministic fingerprint of n."""
    import hashlib
    code, j = _get_paillier(client)
    assert code == 200, "Paillier endpoint not reachable"
    n_hex = j.get("nHex") or j.get("n_hex")
    n = int(n_hex, 16)
    expected = "paillier-" + hashlib.sha256(f"paillier|{n}".encode()).hexdigest()[:12]
    assert j["key_id"] == expected, f"key_id mismatch: {j['key_id']} vs {expected}"


@pytest.mark.skipif(os.environ.get("REQUIRE_2048") != "1",
                    reason="Set REQUIRE_2048=1 in CI to enforce production minimum size")
def test_paillier_bits_minimum_for_prod(client):
    """✅ In CI 'prod mode' enforce >=2048 bits."""
    code, j = _get_paillier(client)
    assert code == 200, "Paillier endpoint not reachable"
    n_hex = j.get("nHex") or j.get("n_hex")
    bits = int(n_hex, 16).bit_length()
    assert bits >= 2048, f"Production Paillier modulus too small: {bits} bits"
