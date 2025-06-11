import os
import sys
import pytest
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add base project path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from models.db import db as real_db
from models.issued_token import IssuedToken

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

def test_create_token(session):
    token = IssuedToken(token_hash="abc123")
    session.add(token)
    session.commit()

    result = session.query(IssuedToken).filter_by(token_hash="abc123").first()
    assert result is not None
    assert result.used is False
    assert isinstance(result.issued_at, datetime)

def test_token_uniqueness_constraint(session):
    token1 = IssuedToken(token_hash="uniquehash")
    token2 = IssuedToken(token_hash="uniquehash")

    session.add(token1)
    session.commit()

    with pytest.raises(Exception):
        session.add(token2)
        session.commit()

def test_update_token_status(session):
    token = IssuedToken(token_hash="changeme")
    session.add(token)
    session.commit()

    token.used = True
    session.commit()

    updated = session.query(IssuedToken).filter_by(token_hash="changeme").first()
    assert updated.used is True

def test_delete_token(session):
    token = IssuedToken(token_hash="deletethis")
    session.add(token)
    session.commit()

    session.delete(token)
    session.commit()

    deleted = session.query(IssuedToken).filter_by(token_hash="deletethis").first()
    assert deleted is None

def test_token_serialization(session):
    token = IssuedToken(token_hash="serialize_me", used=True)
    session.add(token)
    session.commit()

    token_obj = session.query(IssuedToken).filter_by(token_hash="serialize_me").first()

    token_dict = {
        "id": token_obj.id,
        "token_hash": token_obj.token_hash,
        "used": token_obj.used,
        "issued_at": token_obj.issued_at.isoformat()
    }

    assert token_dict["token_hash"] == "serialize_me"
    assert token_dict["used"] is True
    assert "issued_at" in token_dict
