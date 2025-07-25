import os
import sys
import pytest
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add path to project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import models and database
from models.db import db as real_db
from models.voter import Voter

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

# ---------- Tests ----------

def test_create_voter_instance(session):
    voter = Voter(email_hash="abc123", public_key="my_public_key")
    session.add(voter)
    session.commit()

    queried = session.query(Voter).filter_by(email_hash="abc123").first()
    assert queried is not None
    assert queried.public_key == "my_public_key"
    assert queried.is_verified is False
    assert queried.logged_in is False
    if hasattr(queried, "vote_status"):
        assert queried.vote_status is False
    if hasattr(queried, "has_token"):
        assert queried.has_token is False
    assert isinstance(queried.created_at, datetime)

def test_unique_email_constraint(session):
    voter1 = Voter(email_hash="uniquehash", public_key="key1")
    voter2 = Voter(email_hash="uniquehash", public_key="key2")

    session.add(voter1)
    session.commit()

    with pytest.raises(Exception):  # Unique constraint error
        session.add(voter2)
        session.commit()

def test_optional_fields(session):
    voter = Voter(email_hash="opt123")
    session.add(voter)
    session.commit()

    queried = session.query(Voter).filter_by(email_hash="opt123").first()
    assert queried.verification_token is None
    assert queried.totp_secret is None
    assert queried.last_login_ip is None
    assert queried.last_login_at is None
    assert queried.last_2fa_at is None

def test_update_voter_fields(session):
    voter = Voter(email_hash="update123", public_key="original")
    session.add(voter)
    session.commit()

    voter_to_update = session.query(Voter).filter_by(email_hash="update123").first()
    voter_to_update.logged_in = True
    voter_to_update.public_key = "updated"
    session.commit()

    updated = session.query(Voter).filter_by(email_hash="update123").first()
    assert updated.logged_in is True
    assert updated.public_key == "updated"

def test_delete_voter(session):
    voter = Voter(email_hash="delete123")
    session.add(voter)
    session.commit()

    session.delete(voter)
    session.commit()

    deleted = session.query(Voter).filter_by(email_hash="delete123").first()
    assert deleted is None

def test_voter_serialization(session):
    voter = Voter(
        email_hash="serialize123",
        public_key="some_key",
        verification_token="abc",
        is_verified=True,
        logged_in=True,
        totp_secret="TOTPSECRET123"
    )
    session.add(voter)
    session.commit()

    v = session.query(Voter).filter_by(email_hash="serialize123").first()

    voter_dict = {
        "email_hash": v.email_hash,
        "public_key": v.public_key,
        "is_verified": v.is_verified,
        "logged_in": v.logged_in,
        "totp_secret": v.totp_secret,
        "last_login_ip": v.last_login_ip
    }

    if hasattr(v, "vote_status"):
        voter_dict["vote_status"] = v.vote_status
        assert voter_dict["vote_status"] is False

    assert voter_dict["email_hash"] == "serialize123"
    assert voter_dict["is_verified"] is True
