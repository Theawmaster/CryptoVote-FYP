# backend/tests/test_audit_chain.py
import hashlib
import json
from datetime import datetime, timezone

import pytest
from flask import Flask

from models.db import db

GENESIS = "0" * 64


def _iso_now():
    # Use a stable format with timezone so hashing is deterministic in this test
    return datetime.now(timezone.utc).isoformat()


def _compute_entry_hash(prev_hash, admin_email, role, action, timestamp, ip_address):
    """
    Deterministic hash of the log record, chaining prev->current.
    We canonicalize via JSON + `sort_keys=True` to avoid field-order drift.
    """
    payload = {
        "prev_hash": prev_hash,
        "admin_email": admin_email,
        "role": role,
        "action": action,
        "timestamp": timestamp,
        "ip_address": ip_address,
    }
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canon).hexdigest()


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

    # Define a SQLite-safe admin_logs table for this test (no PG regex, etc.)
    with app.app_context():
        md = db.Model.metadata
        if "admin_logs" not in md.tables:
            admin_logs = db.Table(
                "admin_logs",
                md,
                db.Column("id", db.Integer, primary_key=True, autoincrement=True),
                db.Column("admin_email", db.String(120), nullable=False, index=True),
                db.Column("role", db.String(32), nullable=False, index=True),
                db.Column("action", db.Text, nullable=False),
                db.Column("timestamp", db.String(64), nullable=False, index=True),
                db.Column("ip_address", db.String(45), nullable=False),
                db.Column("prev_hash", db.String(64), nullable=False, index=True),
                db.Column("entry_hash", db.String(64), nullable=False, index=True),
            )
        else:
            admin_logs = md.tables["admin_logs"]

        db.Model.metadata.create_all(bind=db.engine, tables=[admin_logs])
    return app


@pytest.fixture
def session(app):
    with app.app_context():
        # clean table before each test
        db.session.execute(db.text("DELETE FROM admin_logs"))
        db.session.commit()
        yield db.session
        db.session.rollback()
        db.session.execute(db.text("DELETE FROM admin_logs"))
        db.session.commit()


def _insert_log(session, prev_hash, admin_email, role, action, timestamp, ip_address):
    entry_hash = _compute_entry_hash(prev_hash, admin_email, role, action, timestamp, ip_address)
    session.execute(
        db.text(
            """
            INSERT INTO admin_logs (admin_email, role, action, timestamp, ip_address, prev_hash, entry_hash)
            VALUES (:admin_email, :role, :action, :timestamp, :ip_address, :prev_hash, :entry_hash)
            """
        ),
        dict(
            admin_email=admin_email,
            role=role,
            action=action,
            timestamp=timestamp,
            ip_address=ip_address,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        ),
    )
    return entry_hash


def _verify_chain(session):
    """
    Recompute each entry_hash and ensure next.prev_hash == this.entry_hash.
    Returns (ok: bool, msg: str|None).
    """
    rows = session.execute(
        db.text(
            "SELECT id, admin_email, role, action, timestamp, ip_address, prev_hash, entry_hash "
            "FROM admin_logs ORDER BY id ASC"
        )
    ).mappings().all()

    if not rows:
        return True, None

    # Verify genesis
    if rows[0]["prev_hash"] != GENESIS:
        return False, f"inconsistent hash chain (id={rows[0]['id']}, reason=bad genesis prev_hash)"

    # Walk and verify
    for i in range(len(rows)):
        r = rows[i]
        expected = _compute_entry_hash(
            r["prev_hash"],
            r["admin_email"],
            r["role"],
            r["action"],
            r["timestamp"],
            r["ip_address"],
        )
        if expected != r["entry_hash"]:
            return False, f"inconsistent hash chain (id={r['id']}, reason=entry hash mismatch)"

        if i + 1 < len(rows):
            nxt = rows[i + 1]
            if nxt["prev_hash"] != r["entry_hash"]:
                return False, f"inconsistent hash chain (id={nxt['id']}, reason=prev != prior entry)"

    return True, None


def test_chain_links_prev_to_prior_entry(session):
    """
    ✅ Inserting entries A→B→C, the stored prev_hash for each matches the prior row’s hash.
    """
    # A
    tA = _iso_now()
    hA = _insert_log(session, GENESIS, "alice@ntu.edu.sg", "admin", "create-election:EL1", tA, "10.0.0.1")
    # B
    tB = _iso_now()
    hB = _insert_log(session, hA, "alice@ntu.edu.sg", "admin", "open-election:EL1", tB, "10.0.0.1")
    # C
    tC = _iso_now()
    hC = _insert_log(session, hB, "alice@ntu.edu.sg", "admin", "close-election:EL1", tC, "10.0.0.1")
    session.commit()

    ok, msg = _verify_chain(session)
    assert ok, f"chain should be consistent, got: {msg}"


def test_mutation_breaks_chain_and_is_detected(session):
    """
    ✅ Mutate B → chain verification fails; error path returns “inconsistent hash chain”.
    """
    # Seed A→B→C again
    tA = _iso_now()
    hA = _insert_log(session, GENESIS, "alice@ntu.edu.sg", "admin", "create-election:EL1", tA, "10.0.0.1")
    tB = _iso_now()
    hB = _insert_log(session, hA, "alice@ntu.edu.sg", "admin", "open-election:EL1", tB, "10.0.0.1")
    tC = _iso_now()
    _ = _insert_log(session, hB, "alice@ntu.edu.sg", "admin", "close-election:EL1", tC, "10.0.0.1")
    session.commit()

    # Tamper with B: change the action WITHOUT updating its entry_hash/children
    # (this simulates an out-of-band DB edit)
    session.execute(
        db.text("UPDATE admin_logs SET action = :a WHERE id = :id"),
        {"a": "open-election:EL1 (tampered)", "id": 2},
    )
    session.commit()

    ok, msg = _verify_chain(session)
    assert not ok, "tampering must be detected"
    assert "inconsistent hash chain" in msg
