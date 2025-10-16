# backend/tests/test_suspicious_endpoints.py
import pytest
from flask import Flask
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from models.db import db
from models.voter import Voter
from models.suspicious_activity import SuspiciousActivity


# blueprint under test
from routes.admin import security_routes as sec_routes  # bp is sec_routes.bp

SGT = ZoneInfo("Asia/Singapore")


# ------------------------
# App / DB setup
# ------------------------
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
    app.register_blueprint(sec_routes.bp)  # routes: /security/...

    with app.app_context():
        # Create only the tables we need for these tests
        db.Model.metadata.create_all(
            bind=db.engine,
            tables=[Voter.__table__, SuspiciousActivity.__table__],
        )

    return app


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


def _admin_login(client, app, email_hash=None):
    """
    Create a fully-authorized admin and mirror everything the guard could check:
    - Voter row exists with vote_role='admin'
    - is_verified=True, logged_in=True, logged_in_2fa=True
    - Session contains email/email_hash/role and flags (twofa=True etc.)
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    SGT = ZoneInfo("Asia/Singapore")

    # Use a 64-hex string so any “sha256-like” sanity checks pass
    if not email_hash:
        email_hash = "ab" * 32  # 64 hex chars

    with app.app_context():
        v = Voter.query.filter_by(email_hash=email_hash).first()
        if not v:
            v = Voter(
                email_hash=email_hash,
                vote_role="admin",
                is_verified=True,
                logged_in=True,
                logged_in_2fa=True,
                last_login_at=datetime.now(SGT),
                last_2fa_at=datetime.now(SGT),
            )
            db.session.add(v)
        else:
            v.vote_role = "admin"
            v.is_verified = True
            v.logged_in = True
            v.logged_in_2fa = True
            v.last_login_at = datetime.now(SGT)
            v.last_2fa_at = datetime.now(SGT)
        db.session.commit()

    # Mirror flags into the session so guards that read session also pass
    with client.session_transaction() as s:
        s["email"] = email_hash         # some guards read "email"
        s["email_hash"] = email_hash    # some guards read "email_hash"
        s["role"] = "admin"
        s["is_verified"] = True
        s["logged_in"] = True
        s["logged_in_2fa"] = True
        s["twofa"] = True               # if the guard checks this one specifically

def _seed_rows(app):
    """Seed 4 rows with varied email/ip/reason/time windows."""
    now = datetime.now(SGT)
    rows = [
        dict(  # within 24h
            email="alice@ntu.edu.sg",
            ip_address="1.1.1.1",
            reason="many failures",
            route_accessed="/login",
            timestamp=now - timedelta(hours=1),
        ),
        dict(  # 2 days ago
            email="bob@ntu.edu.sg",
            ip_address="2.2.2.2",
            reason="vpn anomaly",
            route_accessed="/register",
            timestamp=now - timedelta(days=2),
        ),
        dict(  # within 30 minutes
            email=None,
            ip_address="3.3.3.3",
            reason="tor exit",
            route_accessed="/login",
            timestamp=now - timedelta(minutes=10),
        ),
        dict(  # ~26 hours ago (outside last-24h)
            email="alice@ntu.edu.sg",
            ip_address="1.1.1.1",
            reason="weird UA",
            route_accessed="/admin",
            timestamp=now - timedelta(hours=26),
        ),
    ]
    with app.app_context():
        db.session.add_all(SuspiciousActivity(**r) for r in rows)
        db.session.commit()


# ------------------------
# Tests
# ------------------------

def test_filters_and_sgt_timestamps_in_json(client, app):
    _admin_login(client, app)
    _seed_rows(app)

    # email filter (alice) -> 2 rows (1 within 24h, 1 older)
    r = client.get("/security/suspicious?email=alice@ntu.edu.sg")
    assert r.status_code == 200
    data = r.get_json()
    assert data["total"] == 2
    # timestamps must be SGT (+08:00)
    assert all("+08:00" in item["timestamp"] for item in data["items"])

    # ip filter (3.3.3.3) -> 1 row
    r = client.get("/security/suspicious?ip=3.3.3.3")
    assert r.status_code == 200 and r.get_json()["total"] == 1

    # reason substring (vpn) -> 1 row
    r = client.get("/security/suspicious?reason=vpn")
    assert r.status_code == 200 and r.get_json()["total"] == 1

    # since (last 12h) -> rows within 12h (1h + 10m) = 2
    since = (datetime.now(SGT) - timedelta(hours=12)).isoformat()
    r = client.get(f"/security/suspicious?since={since}")
    assert r.status_code == 200 and r.get_json()["total"] == 2

    # until (older than 24h) -> 2 rows (2d + 26h)
    until = (datetime.now(SGT) - timedelta(hours=24)).isoformat()
    r = client.get(f"/security/suspicious?until={until}")
    assert r.status_code == 200 and r.get_json()["total"] == 2

    # since_minutes=30 -> only the 10m row
    r = client.get("/security/suspicious?since_minutes=30")
    assert r.status_code == 200 and r.get_json()["total"] == 1


def test_csv_export_includes_sgt_and_download_headers(client, app):
    _admin_login(client, app)
    # fresh dataset
    with app.app_context():
        db.session.query(SuspiciousActivity).delete()
        db.session.add(
            SuspiciousActivity(
                email="ops@ntu.edu.sg",
                ip_address="8.8.8.8",
                reason="burst traffic",
                route_accessed="/login",
                timestamp=datetime.now(SGT) - timedelta(minutes=5),
            )
        )
        db.session.commit()

    r = client.get("/security/suspicious.csv")
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("text/csv")
    assert "attachment; filename=suspicious.csv" in r.headers.get("Content-Disposition", "")
    body = r.data.decode("utf-8")
    # header plus one data line
    assert "id,email,ip_address,reason,route_accessed,timestamp" in body
    # SGT offset present (+08:00)
    assert "+08:00" in body, "CSV timestamps should be in SGT"


def test_pdf_export_downloads_and_mentions_sgt(client, app):
    _admin_login(client, app)
    r = client.get("/security/suspicious.pdf")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/pdf"
    disp = r.headers.get("Content-Disposition", "")
    assert "suspicious.pdf" in disp
    # The PDF includes a "Generated: ... SGT" header line; look for ASCII "SGT"
    assert b"SGT" in r.data, "PDF should print SGT in the generated-at header"


def test_last_24h_count_endpoint(client, app):
    _admin_login(client, app)
    # clear & seed precise windows
    with app.app_context():
        db.session.query(SuspiciousActivity).delete()
        now = datetime.now(SGT)
        inside = now - timedelta(hours=1)
        outside = now - timedelta(hours=30)
        db.session.add_all(
            [
                SuspiciousActivity(
                    email="a@ntu", ip_address="1.1.1.1", reason="x", route_accessed="/", timestamp=inside
                ),
                SuspiciousActivity(
                    email="b@ntu", ip_address="2.2.2.2", reason="y", route_accessed="/", timestamp=outside
                ),
                SuspiciousActivity(
                    email=None, ip_address="3.3.3.3", reason="z", route_accessed="/", timestamp=now - timedelta(minutes=10)
                ),
            ]
        )
        db.session.commit()

    r = client.get("/security/suspicious/count")
    assert r.status_code == 200
    assert r.get_json()["count"] == 2  # last-24h includes 1h + 10m rows
