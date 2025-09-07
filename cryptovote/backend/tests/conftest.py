# backend/tests/conftest.py
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
from flask import Flask
from phe import paillier

# Ensure "backend/" is on sys.path so `routes.cast_vote` imports work
BACKEND_DIR = Path(__file__).resolve().parents[1]  # .../backend
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import routes.cast_vote as cv  # the blueprint under test


@pytest.fixture
def app(monkeypatch):
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret")

    # Small key for test speed
    pub, _priv = paillier.generate_paillier_keypair(n_length=256)

    # ---- Stubs the route expects ----

    # Auth: always returns a logged-in voter
    class _VoterQ:
        def filter_by(self, **kw): return self
        def first(self): return NS(id=1, is_verified=True, logged_in=True)
    monkeypatch.setattr(cv, "Voter", NS(query=_VoterQ()))

    # EncryptedCandidateVote model stub (capture created rows)
    class _EncVote:
        # Class-level attrs used in query expressions:
        id = object()
        token_hash = "token_hash"  # sentinel; our .filter stub ignores the expression anyway

        def __init__(self, candidate_id, vote_ciphertext, vote_exponent, token_hash, cast_at, election_id):
            self.candidate_id = candidate_id
            self.vote_ciphertext = vote_ciphertext
            self.vote_exponent = vote_exponent
            self.token_hash = token_hash
            self.cast_at = cast_at
            self.election_id = election_id
    monkeypatch.setattr(cv, "EncryptedCandidateVote", _EncVote)

    # VES (double-vote guard) stub
    class _VESQ:
        def filter_by(self, **kw): return self
        def first(self): return None
        def one_or_none(self): return None
    class _VES:
        def __init__(self, voter_id, election_id):
            self.voter_id = voter_id
            self.election_id = election_id
            self.voted_at = None
        query = _VESQ()
    monkeypatch.setattr(cv, "VES", _VES)

    # DB session stub with two query shapes: candidates + token reuse
    class _Sess:
        def __init__(self): self._adds = []
        def get(self, Model, election_id):
            if Model is cv.Election:
                return NS(
                    id=election_id,
                    rsa_key_id="rsa-demo",
                    is_active=True,
                    has_started=True,
                    has_ended=False,
                )
            return None
        def query(self, what):
            cand_id_attr    = getattr(cv.Candidate, "id", object())
            encvote_id_attr = getattr(cv.EncryptedCandidateVote, "id", object())

            class _Q:
                def __init__(self, mode): self.mode = mode
                def join(self, *a, **k): return self
                def filter(self, *a, **k): return self
                def all(self):
                    if self.mode == "cands":
                        return [NS(id="c1"), NS(id="c2"), NS(id="c3")]
                    return []
                def first(self):
                    # never signal token reuse in these unit tests
                    return None

            mode = "cands" if what is cand_id_attr else \
                   "encvote_ids" if what is encvote_id_attr else "other"
            return _Q(mode)
        def add(self, obj): self._adds.append(obj)
        def commit(self): pass
    sess = _Sess()
    monkeypatch.setattr(cv.db, "session", sess)

    # Crypto hooks inside the route
    monkeypatch.setattr(cv, "parse_and_verify_signature", lambda *a, **k: (True, None, None))
    monkeypatch.setattr(cv, "load_rsa_pubkey", lambda *a, **k: object())
    monkeypatch.setattr(cv, "load_paillier_public_key", lambda: pub)

    # 🔑 Keep the E2EE unit test focused on ciphertext storage only
    monkeypatch.setattr(cv, "mark_voted", lambda *a, **k: None)

    # Register the blueprint and expose captured inserts for assertions
    app.register_blueprint(cv.cast_vote_bp)
    app._pub = pub
    app._added = sess._adds
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    """Use in tests: call login() before POSTing."""
    def _go():
        with client.session_transaction() as s:
            s["email"] = "unit@test"
    return _go
