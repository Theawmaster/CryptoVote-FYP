# backend/tests/test_receipt.py
import pytest
from flask import Flask
from models.db import db

# Module under test
import routes.receipt as receipt_routes
from routes.receipt import receipt_bp

# Skip if ReportLab isn’t installed
try:
    import reportlab  # noqa: F401
    HAVE_PDF = True
except Exception:
    HAVE_PDF = False

pytestmark = pytest.mark.skipif(
    not HAVE_PDF, reason="ReportLab not installed; PDF receipt tests skipped"
)

@pytest.fixture
def app(monkeypatch):
    """
    Minimal Flask app for /voter/receipt.
    - Disable ReportLab page compression so strings like 'SGT' are visible in PDF bytes.
    - Init in-memory sqlite so accidental db.session usage won’t explode.
    """
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Patch Canvas to turn OFF page compression (so our test can find strings in bytes)
    if getattr(receipt_routes, "HAVE_PDF", False):
        OriginalCanvas = receipt_routes.canvas.Canvas
        def CanvasNoCompress(*args, **kwargs):
            kwargs.setdefault("pageCompression", 0)
            return OriginalCanvas(*args, **kwargs)
        monkeypatch.setattr(receipt_routes.canvas, "Canvas", CanvasNoCompress, raising=False)

    db.init_app(app)
    with app.app_context():
        try:
            db.Model.metadata.create_all(bind=db.engine)
        except Exception:
            pass

    app.register_blueprint(receipt_bp)
    return app

@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c

def _assert_no_choice_leak(pdf_bytes: bytes):
    """Anti-coercion: the PDF must not contain candidate/ballot terms."""
    lower = pdf_bytes.lower()
    assert b"candidate" not in lower
    assert b"ballot" not in lower

def test_receipt_pdf_contains_minimum_fields_and_no_choice_info(client):
    """
    PDF must contain election name, election id, timestamp (with literal 'SGT'),
    and must not include choice-revealing terms.
    """
    r = client.get("/voter/receipt", query_string={
        "election_name": "Student Council 2025",
        "election_id": "EL-TEST-123",
        # no tracker — keeps optional WBB lookup path inactive
    })
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("application/pdf")
    assert "vote_receipt_" in r.headers.get("Content-Disposition", "")

    data = r.data
    assert b"Student Council 2025" in data
    assert b"Election ID: EL-TEST-123" in data
    assert b"Timestamp:" in data
    # Compression disabled => 'SGT' is visible in bytes
    assert b"SGT" in data

    _assert_no_choice_leak(data)

def test_receipt_pdf_includes_tracker_line_without_leaking_choices(client):
    """
    With only a tracker (no election_id), the PDF shows the tracker line and generic
    inclusion copy, without touching DB or leaking choices.
    """
    r = client.get("/voter/receipt", query_string={
        "election_name": "General Election",
        "tracker": "TRK-XYZ-999",
        # omit election_id -> optional WBB lookup path remains idle
    })
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("application/pdf")

    data = r.data
    assert b"Tracker: TRK-XYZ-999" in data
    # Our copy mentions inclusion generically (e.g., "Inclusion: ...")
    assert b"Inclusion" in data or b"Not found" in data

    _assert_no_choice_leak(data)
