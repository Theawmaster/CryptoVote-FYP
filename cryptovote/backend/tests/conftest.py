# backend/tests/conftest.py
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest
from flask import Flask
from phe import paillier

# Make sure backend/ is importable
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

@pytest.fixture
def app(monkeypatch):
    """
    App fixture for cast-vote E2EE tests:
    - DO NOT replace the EncryptedCandidateVote class globally.
    - Patch only the cast_vote route module to use a fake session and crypto stubs.
    """
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret")

    # small key for speed
    pub, _priv = paillier.generate_paillier_keypair(n_length=256)

    # Import inside the fixture so our patches are local to this app
    import routes.cast_vote as cv

    # --------------------------- Model/Test Stubs ---------------------------
    # Always-authenticated voter for this route
    class _VoterQ:
        def filter_by(self, **kw): return self
        def first(self): return NS(id=1, is_verified=True, logged_in=True, logged_in_2fa=True)
    monkeypatch.setattr(cv, "Voter", NS(query=_VoterQ()))

    # VES (double-vote guard)
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

    # Minimal candidates / election models the route touches
    class _Candidate:
        id = object()
        election_id = object()
    monkeypatch.setattr(cv, "Candidate", _Candidate)

    class _Election: ...
    monkeypatch.setattr(cv, "Election", _Election)

    class _PosAttr:
        def desc(self): return self
    class _WbbEntry:
        position = _PosAttr()
        def __init__(self, election_id, tracker, token_hash, position, leaf_hash, commitment_hash):
            self.election_id = election_id
            self.tracker = tracker
            self.token_hash = token_hash
            self.position = position
            self.leaf_hash = leaf_hash
            self.commitment_hash = commitment_hash
    monkeypatch.setattr(cv, "WbbEntry", _WbbEntry)

    # --------------------------- Fake DB Session ---------------------------
    class _Sess:
        def __init__(self):
            self._adds = []

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

        def query(self, *entities):
            what = entities[0] if entities else None
            cand_id_attr      = getattr(cv.Candidate, "id", None)
            from models.encrypted_candidate_vote import EncryptedCandidateVote as ECV
            encvote_id_attr   = getattr(ECV, "id", None)
            wbb_position_attr = getattr(cv.WbbEntry, "position", None)

            if what is cand_id_attr:
                mode = "cands"
            elif what is encvote_id_attr:
                mode = "encvote_ids"
            elif what is wbb_position_attr:
                mode = "wbbpos"
            else:
                mode = "other"

            class _Q:
                def __init__(self, mode):
                    self.mode = mode
                def filter(self, *a, **k):    return self
                def filter_by(self, **k):     return self
                def order_by(self, *a, **k):  return self
                def join(self, *a, **k):      return self
                def all(self):
                    return [NS(id="c1"), NS(id="c2"), NS(id="c3")] if self.mode == "cands" else []
                def first(self):
                    return None  # no reuse; so next WBB position is 0
            return _Q(mode)

        def add(self, obj):
            self._adds.append(obj)

        def commit(self): pass

    sess = _Sess()
    monkeypatch.setattr(cv.db, "session", sess)

    # ----------------------- Crypto stubs & helpers ------------------------
    monkeypatch.setattr(cv, "parse_and_verify_signature", lambda *a, **k: (True, None, None), raising=True)
    monkeypatch.setattr(cv, "load_rsa_pubkey", lambda *a, **k: object(), raising=True)
    monkeypatch.setattr(cv, "load_paillier_public_key", lambda: pub, raising=True)
    monkeypatch.setattr(cv, "mark_voted", lambda *a, **k: None, raising=True)

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
    def _go():
        with client.session_transaction() as s:
            s["email"] = "unit@test"
    return _go
