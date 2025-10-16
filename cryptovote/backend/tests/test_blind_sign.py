# backend/tests/test_blind_sign.py
import os, json, hashlib, random, importlib
from types import SimpleNamespace as NS
import pytest
from flask import Flask

# ensure backend/ is importable
import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# -------- tiny RSA helpers (test-only) --------
def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def _rsa_make_keypair():
    p, q = 61153, 65003  # small primes; fast tests
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 65537
    d = pow(e, -1, phi)
    return NS(n=n, e=e, d=d)

def _sha256_int(msg: bytes, n: int) -> int:
    return int.from_bytes(hashlib.sha256(msg).digest(), "big") % n

def _rsa_blind(m, n, e):
    while True:
        r = random.randrange(2, n - 1)
        if _gcd(r, n) == 1:
            break
    blinded = (m * pow(r, e, n)) % n
    r_inv = pow(r, -1, n)
    return blinded, r, r_inv

def _rsa_unblind(signed_blinded, r_inv, n):
    return (signed_blinded * r_inv) % n


@pytest.fixture
def app(monkeypatch):
    # 1) neutralize role_required BEFORE importing the route (decorator applied at import time)
    try:
        import utilities.auth_utils as auth_utils
        def _noop_role_required(_role):
            def deco(f): return f
            return deco
        monkeypatch.setattr(auth_utils, "role_required", _noop_role_required, raising=False)
    except Exception:
        pass

    # 2) import/reload the route so it picks up noop decorator
    import routes.blind_sign as bs
    bs = importlib.reload(bs)

    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret")

    # RSA key for test signing
    kp = _rsa_make_keypair()
    app._rsa = kp

    # ---- db + models stubs ----
    class _Sess:
        def __init__(self): self._adds = []
        def add(self, obj): self._adds.append(obj)
        def commit(self): pass
        def rollback(self): pass
        def query(self, *entities):
            # returns an object with .filter(...).first()
            class _Q:
                def filter(self, *a, **k): return self
                def first(self): return None
            return _Q()
    sess = _Sess()

    class _IssuedToken:
        def __init__(self, token_hash, used, issued_at):
            self.token_hash, self.used, self.issued_at = token_hash, used, issued_at

    class _VoterQ:
        def filter_by(self, **kw): return self
        def first(self):  # logged-in + verified
            return NS(id=1, is_verified=True, logged_in=True)

    # VES stub: must support db.session.query(VES.id), comparisons, and instantiation
    class _Attr:
        def __eq__(self, other):     # supports VES.voter_id == ...
            return self
        def isnot(self, other):      # supports VES.token_issued_at.isnot(None)
            return self

    class _VESQ:
        def filter_by(self, **kw): return self
        def one_or_none(self):      return None

    class _VES:
        # ---- class-level attributes used in SQLAlchemy-ish expressions ----
        id              = object()
        voter_id        = _Attr()
        election_id     = _Attr()
        token_issued_at = _Attr()
        query           = _VESQ()

        # ---- instance-level for mark_token_issued(...) ----
        def __init__(self, voter_id, election_id):
            self.voter_id        = voter_id
            self.election_id     = election_id
            self.token_issued_at = None


    class _ElectionQ:
        def __init__(self, expected_id): self.expected_id = expected_id
        def filter_by(self, **kw):
            self.kw = kw; return self
        def first(self):
            if self.kw.get("id") == self.expected_id and self.kw.get("is_active") is True:
                return NS(id=self.expected_id, is_active=True, rsa_key_id="rsa-demo")
            return None
    class _Election:
        query = _ElectionQ(expected_id="E")

    # Patch into reloaded module
    monkeypatch.setattr(bs, "db", NS(session=sess))
    monkeypatch.setattr(bs, "IssuedToken", _IssuedToken)
    monkeypatch.setattr(bs, "Voter", NS(query=_VoterQ()))
    monkeypatch.setattr(bs, "VES", _VES)
    monkeypatch.setattr(bs, "Election", _Election)

    # Patch signer to use our test RSA key
    def _sign_blinded_token(blinded_int, rsa_key_id=None):
        return pow(int(blinded_int), kp.d, kp.n)
    monkeypatch.setattr(bs, "sign_blinded_token", _sign_blinded_token)

    app.register_blueprint(bs.blind_sign_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def _login(client):
    with client.session_transaction() as s:
        s["email"] = "unit@test"  # route checks this


# -------- tests: exactly the 3 you asked for --------
def test_blind_sign_and_verify(client, app):
    _login(client)
    n, e = app._rsa.n, app._rsa.e

    token = os.urandom(16)
    m = _sha256_int(token, n)
    blinded, _, r_inv = _rsa_blind(m, n, e)

    payload = {"blinded_token_hex": format(blinded, "x"), "rsa_key_id": "rsa-demo"}
    resp = client.post("/elections/E/blind-sign",
                       data=json.dumps(payload),
                       content_type="application/json")
    assert resp.status_code == 200, resp.data

    signed_blinded = int(resp.get_json()["signed_blinded_token_hex"], 16)
    s = _rsa_unblind(signed_blinded, r_inv, n)
    assert pow(s, e, n) == m  # RSA_verify(SHA256(token), s)

def test_invalid_blinded_token_hex_returns_400(client):
    _login(client)
    payload = {"blinded_token_hex": "not-hex", "rsa_key_id": "rsa-demo"}
    resp = client.post("/elections/E/blind-sign",
                       data=json.dumps(payload),
                       content_type="application/json")
    assert resp.status_code == 400, resp.data

def test_mismatched_rsa_key_id_returns_400(client, app):
    _login(client)
    n, e = app._rsa.n, app._rsa.e
    m = 12345 % n
    blinded, _, _ = _rsa_blind(m, n, e)
    payload = {"blinded_token_hex": format(blinded, "x"), "rsa_key_id": "wrong-id"}
    resp = client.post("/elections/E/blind-sign",
                       data=json.dumps(payload),
                       content_type="application/json")
    assert resp.status_code == 400, resp.data
