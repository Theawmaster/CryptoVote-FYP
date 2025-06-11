import os
import sys
import pytest
from datetime import datetime, timedelta
from flask import Flask

# Add project root to import paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from models.db import db as real_db
from models.election import Election

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

def test_create_election(session):
    election = Election(
        id="election2025",
        name="Student Council 2025",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(days=1),
        is_active=True,
        has_started=True,
        has_ended=False,
        tally_generated=False
    )
    session.add(election)
    session.commit()

    result = session.query(Election).filter_by(id="election2025").first()
    assert result is not None
    assert result.name == "Student Council 2025"
    assert result.is_active is True
    assert result.has_started is True
    assert result.has_ended is False
    assert result.tally_generated is False

def test_update_election_flags(session):
    election = Election(
        id="election2026",
        name="School Election 2026",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(days=2),
        is_active=False
    )
    session.add(election)
    session.commit()

    # Update status flags
    election.has_started = True
    election.has_ended = True
    election.tally_generated = True
    session.commit()

    updated = session.query(Election).filter_by(id="election2026").first()
    assert updated.has_started is True
    assert updated.has_ended is True
    assert updated.tally_generated is True

def test_delete_election(session):
    election = Election(
        id="election2027",
        name="To Be Deleted",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=12)
    )
    session.add(election)
    session.commit()

    session.delete(election)
    session.commit()

    deleted = session.query(Election).filter_by(id="election2027").first()
    assert deleted is None

def test_default_fields(session):
    now = datetime.utcnow()
    election = Election(
        id="election2028",
        name="Default Check Election",
        end_time=now + timedelta(days=1)
    )
    session.add(election)
    session.commit()

    result = session.query(Election).filter_by(id="election2028").first()
    assert result is not None
    assert result.is_active is False
    assert result.has_started is False
    assert result.has_ended is False
    assert result.tally_generated is False
    assert isinstance(result.start_time, datetime)
