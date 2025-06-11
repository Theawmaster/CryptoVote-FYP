import os
import sys
import pytest
from datetime import datetime
from flask import Flask

# Add project root to import paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from models.db import db as real_db
from models.encrypted_candidate_vote import EncryptedCandidateVote

# ---------- Fixtures ----------

@pytest.fixture(scope="module")
def test_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    real_db.init_app(app)

    with app.app_context():
        real_db.create_all()
        yield app
        real_db.drop_all()

@pytest.fixture
def session(test_app):
    with test_app.app_context():
        yield real_db.session
        real_db.session.rollback()

# ---------- Tests ----------

def test_create_encrypted_vote(session):
    vote = EncryptedCandidateVote(
        candidate_id="candidate123",
        vote_ciphertext="enc(abc123)",
        vote_exponent=2,
        token_hash="tokenhash123"
    )
    session.add(vote)
    session.commit()

    result = session.query(EncryptedCandidateVote).filter_by(candidate_id="candidate123").first()
    assert result is not None
    assert result.vote_ciphertext == "enc(abc123)"
    assert result.vote_exponent == 2
    assert result.token_hash == "tokenhash123"
    assert isinstance(result.cast_at, datetime)

def test_update_vote_ciphertext(session):
    vote = EncryptedCandidateVote(
        candidate_id="candidate456",
        vote_ciphertext="enc(initial)",
        vote_exponent=1,
        token_hash="hash456"
    )
    session.add(vote)
    session.commit()

    vote.vote_ciphertext = "enc(updated)"
    session.commit()

    updated = session.query(EncryptedCandidateVote).filter_by(candidate_id="candidate456").first()
    assert updated.vote_ciphertext == "enc(updated)"

def test_delete_vote(session):
    vote = EncryptedCandidateVote(
        candidate_id="candidate789",
        vote_ciphertext="enc(to_delete)",
        vote_exponent=0,
        token_hash="hash789"
    )
    session.add(vote)
    session.commit()

    session.delete(vote)
    session.commit()

    deleted = session.query(EncryptedCandidateVote).filter_by(candidate_id="candidate789").first()
    assert deleted is None

def test_default_cast_at(session):
    vote = EncryptedCandidateVote(
        candidate_id="candidateDefault",
        vote_ciphertext="enc(default)",
        vote_exponent=1,
        token_hash="defaultHash"
    )
    session.add(vote)
    session.commit()

    result = session.query(EncryptedCandidateVote).filter_by(candidate_id="candidateDefault").first()
    assert isinstance(result.cast_at, datetime)
