import os
import sys
import pytest
from datetime import datetime
from flask import Flask

# 🔧 Set up path to import models
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from models.db import db as real_db
from models.admin_log import AdminLog

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

def test_create_log(session):
    log = AdminLog(
        admin_email="admin@example.com",
        role="admin",
        action="created election",
        timestamp=datetime.utcnow(),
        ip_address="127.0.0.1",
        prev_hash="0" * 64,
        entry_hash="1" * 64
    )
    session.add(log)
    session.commit()

    result = session.query(AdminLog).filter_by(admin_email="admin@example.com").first()
    assert result is not None
    assert result.role == "admin"
    assert result.prev_hash == "0" * 64
    assert result.entry_hash == "1" * 64

def test_update_log_action(session):
    log = AdminLog(
        admin_email="update@example.com",
        role="admin",
        action="initial",
        timestamp=datetime.utcnow(),
        ip_address="127.0.0.1",
        prev_hash="abc",
        entry_hash="def"
    )
    session.add(log)
    session.commit()

    log.action = "updated"
    session.commit()

    updated = session.query(AdminLog).filter_by(admin_email="update@example.com").first()
    assert updated.action == "updated"

def test_delete_log(session):
    log = AdminLog(
        admin_email="delete@example.com",
        role="admin",
        action="delete-me",
        timestamp=datetime.utcnow(),
        ip_address="127.0.0.1",
        prev_hash="prevhash",
        entry_hash="entryhash"
    )
    session.add(log)
    session.commit()

    session.delete(log)
    session.commit()

    deleted = session.query(AdminLog).filter_by(admin_email="delete@example.com").first()
    assert deleted is None

def test_log_serialization_fields(session):
    log = AdminLog(
        admin_email="serial@example.com",
        role="auditor",
        action="checked integrity",
        timestamp=datetime.utcnow(),
        ip_address="192.168.0.1",
        prev_hash="prev123",
        entry_hash="entry456"
    )
    session.add(log)
    session.commit()

    fetched = session.query(AdminLog).filter_by(admin_email="serial@example.com").first()
    assert fetched.timestamp is not None
    assert fetched.admin_email == "serial@example.com"
    assert fetched.prev_hash == "prev123"
    assert fetched.entry_hash == "entry456"
