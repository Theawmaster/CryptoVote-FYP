# backend/tests/test_tally.py
import pytest
from flask import Flask
from phe import paillier

from models.db import db
from models.election import Election, Candidate
import models.encrypted_candidate_vote as ecv_mod
import services.tallying_service as tally_svc
import os, hashlib


def _ensure_mapped_ecv():
    """
    Return (EncryptedCandidateVoteClass, Table) without redefining/overriding
    the real project model. If a stub exists that lacks the backref, attach it.
    """
    ECV = getattr(ecv_mod, "EncryptedCandidateVote", None)

    # Case 1: a class is already present and mapped
    if isinstance(ECV, type) and hasattr(ECV, "__table__"):
        # If a stub lacks the backref, add it so Candidate.votes can resolve.
        if not hasattr(ECV, "candidate"):
            ECV.candidate = db.relationship("Candidate", back_populates="votes")
        return ECV, ECV.__table__

    # Case 2: no class yet — define a minimal mapped class + the backref
    md = db.Model.metadata
    key = "encrypted_candidate_votes"

    if key in md.tables:
        table = md.tables[key]
    else:
        table = db.Table(
            key,
            md,
            db.Column("id", db.Integer, primary_key=True),
            db.Column(
                "candidate_id",
                db.String(64),
                db.ForeignKey("candidates.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            db.Column("vote_ciphertext", db.Text, nullable=False),
            db.Column("vote_exponent", db.Integer, nullable=False, default=0),
            db.Column("token_hash", db.String(64), nullable=True),
            db.Column("cast_at", db.DateTime(timezone=True), server_default=db.func.now()),
            db.Column("election_id", db.String(64), db.ForeignKey("elections.id"), index=True, nullable=False),
        )

    EncryptedCandidateVote = type(
        "EncryptedCandidateVote",
        (db.Model,),
        {
            "__table__": table,
            "candidate": db.relationship("Candidate", back_populates="votes"),
        },
    )
    setattr(ecv_mod, "EncryptedCandidateVote", EncryptedCandidateVote)
    return EncryptedCandidateVote, table


@pytest.fixture(scope="module")
def app():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    with app.app_context():
        ECV, ECV_tbl = _ensure_mapped_ecv()
        # Create only the tables we actually need
        db.Model.metadata.create_all(
            bind=db.engine,
            tables=[Election.__table__, Candidate.__table__, ECV_tbl],
        )
    yield app


@pytest.fixture
def session(app):
    with app.app_context():
        yield db.session
        db.session.rollback()
        # Truncate touched tables between tests
        for tbl in reversed(db.Model.metadata.sorted_tables):
            if tbl.name in {"encrypted_candidate_votes", "candidates", "elections"}:
                db.session.execute(tbl.delete())
        db.session.commit()


@pytest.fixture
def paillier_pair(monkeypatch):
    """Fresh Paillier keypair per test; patch the service to use it."""
    pub, priv = paillier.generate_paillier_keypair()
    monkeypatch.setattr(tally_svc, "load_public_key", lambda: pub, raising=True)
    monkeypatch.setattr(tally_svc, "load_private_key", lambda: priv, raising=True)
    return pub, priv


def _put_enc_vote(session, ECV, candidate_id, election_id, pub, value, token_hash=None):
    enc = pub.encrypt(int(value))
    if token_hash is None:
        # unique per row; satisfies NOT NULL and (election_id, token_hash) uniqueness policies
        rnd = os.urandom(8).hex()
        token_hash = hashlib.sha256(f"{election_id}|{candidate_id}|{value}|{rnd}".encode()).hexdigest()

    row = ECV(
        candidate_id=candidate_id,
        election_id=election_id,
        vote_ciphertext=str(enc.ciphertext()),
        vote_exponent=enc.exponent,
        token_hash=token_hash,
    )
    session.add(row)


def _seed_election(session):
    election = Election(id="EL-TALLY", name="Tally Test", is_active=True)
    db.session.add(election)
    c1 = Candidate(id="C1", name="Alice", election_id=election.id)
    c2 = Candidate(id="C2", name="Bob",   election_id=election.id)
    db.session.add_all([c1, c2])
    db.session.commit()
    return election.id, c1.id, c2.id


def test_tally_homomorphic_sum_and_decrypts_only_aggregates(session, paillier_pair, monkeypatch):
    """
    Seed 3 ballots for 2 candidates: counts -> Alice:2, Bob:1
    Assert: tally_votes() returns exactly those counts, and private_key.decrypt
    is called exactly once per candidate (no per-ballot decrypts).
    """
    pub, priv = paillier_pair
    ECV, _ = _ensure_mapped_ecv()

    # Make sure service queries the real mapped model, not a stub
    monkeypatch.setattr(tally_svc, "EncryptedCandidateVote", ECV, raising=False)

    election_id, c1, c2 = _seed_election(session)

    # Three ballots (one-hot):
    # B1: C1=1, C2=0
    # B2: C1=1, C2=0
    # B3: C1=0, C2=1
    _put_enc_vote(session, ECV, c1, election_id, pub, 1)
    _put_enc_vote(session, ECV, c2, election_id, pub, 0)
    _put_enc_vote(session, ECV, c1, election_id, pub, 1)
    _put_enc_vote(session, ECV, c2, election_id, pub, 0)
    _put_enc_vote(session, ECV, c1, election_id, pub, 0)
    _put_enc_vote(session, ECV, c2, election_id, pub, 1)
    session.commit()

    # Spy: decrypt should be called once per candidate (2), not per vote (6)
    calls = {"n": 0}
    real_decrypt = priv.decrypt

    def spy_decrypt(enc_number):
        calls["n"] += 1
        return real_decrypt(enc_number)

    class SpyPrivKey:
        public_key = priv.public_key
        def decrypt(self, enc_number):
            return spy_decrypt(enc_number)

    monkeypatch.setattr(tally_svc, "load_private_key", lambda: SpyPrivKey(), raising=True)

    result = tally_svc.tally_votes(session, election_id)
    got = {row["candidate_id"]: row["vote_count"] for row in result}

    assert got[c1] == 2 and got[c2] == 1, f"Unexpected tallies: {got}"
    assert calls["n"] == 2, f"decrypt called {calls['n']} times; expected 2 (aggregate only)"
