import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from models.db import db
from models.suspicious_activity import SuspiciousActivity
from flask import Flask

SGT = ZoneInfo("Asia/Singapore")


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True

    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def session(app):
    with app.app_context():
        yield db.session


def test_create_suspicious_activity_full_fields(session):
    entry = SuspiciousActivity(
        email="admin@ntu.edu.sg",
        ip_address="192.168.1.1",
        reason="Unauthorized access",
        route_accessed="/admin/panel"
    )
    session.add(entry)
    session.commit()

    retrieved = SuspiciousActivity.query.first()
    assert retrieved.email == "admin@ntu.edu.sg"
    assert retrieved.ip_address == "192.168.1.1"
    assert retrieved.reason == "Unauthorized access"
    assert retrieved.route_accessed == "/admin/panel"
    assert isinstance(retrieved.timestamp, datetime)


def test_create_suspicious_activity_without_email(session):
    entry = SuspiciousActivity(
        email=None,
        ip_address="10.0.0.2",
        reason="Invalid login attempt",
        route_accessed="/login"
    )
    session.add(entry)
    session.commit()

    retrieved = SuspiciousActivity.query.first()
    assert retrieved.email is None
    assert retrieved.reason == "Invalid login attempt"
    assert retrieved.route_accessed == "/login"


def test_missing_required_fields_should_fail(session):
    incomplete = SuspiciousActivity(
        ip_address="10.0.0.3",
        reason=None,  # Required field set to None
        route_accessed="/vote"
    )
    with pytest.raises(Exception):
        session.add(incomplete)
        session.commit()
