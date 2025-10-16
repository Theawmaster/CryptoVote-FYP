# routes/receipt.py
import os
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, request, make_response

# --- flexible imports (works with both module layouts) ---
try:
    from models.db import db
    from models.wbb_entry import WbbEntry
except Exception:
    from cryptovote.backend.models import db  # type: ignore
    from cryptovote.backend.models.wbb_entry import WbbEntry  # type: ignore

SGT = ZoneInfo("Asia/Singapore")
receipt_bp = Blueprint("receipt", __name__)

# Optional: ReportLab PDF
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    HAVE_PDF = True
except Exception:
    HAVE_PDF = False


def _asset_path(filename: str) -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "assets", filename)


@receipt_bp.get("/voter/receipt")
def voter_receipt():
    # -------- request inputs --------
    election_name = (request.args.get("election_name") or "Election").strip()
    election_id = (request.args.get("election_id") or "-").strip()
    tracker = (request.args.get("tracker") or "").strip()
    ts = datetime.now(SGT).strftime("%d %b %Y, %H:%M %Z")

    # -------- optional WBB check --------
    tracker_ok = False
    index = None
    if tracker and election_id:
        q = db.session.query(WbbEntry).filter_by(
            election_id=election_id
        ).order_by(WbbEntry.position.asc())
        entries = q.all()
        for i, e in enumerate(entries):
            if e.tracker == tracker:
                tracker_ok = True
                index = e.position
                break

    # -------- PDF path --------
    if HAVE_PDF:
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setTitle(f"Vote receipt — {election_name}")

        page_w, page_h = letter
        margin = 56
        y = page_h - margin

        # --- logos (optional) ---
        def draw_logo(path, x, y_top, target_h=36):
            if os.path.exists(path):
                try:
                    img = ImageReader(path)
                    iw, ih = img.getSize()
                    scale = target_h / ih
                    w = iw * scale
                    h = target_h
                    c.drawImage(img, x, y_top - h, width=w, height=h, mask="auto")
                except Exception:
                    pass

        draw_logo(_asset_path("ntu_logo.png"), margin, y)
        draw_logo(_asset_path("cryptovote_logo.png"), page_w - margin - 80, y)
        y -= 60

        # --- title ---
        c.setFont("Helvetica-Bold", 16)
        title = f"{election_name} — Vote received"
        title_w = c.stringWidth(title, "Helvetica-Bold", 16)
        c.drawString((page_w - title_w) / 2, y, title)
        y -= 30

        # --- meta ---
        c.setFont("Helvetica", 12)
        c.drawString(margin, y, f"Timestamp: {ts}"); y -= 18
        c.drawString(margin, y, f"Election ID: {election_id}"); y -= 18

        # --- tracker (NEW) ---
        if tracker:
            c.drawString(margin, y, f"Tracker: {tracker}"); y -= 18
            if tracker_ok:
                c.setFillColorRGB(0.1, 0.5, 0.1)
                c.drawString(margin, y, f"Inclusion: Yes ✓  (index {index})")
                c.setFillColorRGB(0, 0, 0)
            else:
                c.setFillColorRGB(0.7, 0.2, 0.2)
                c.drawString(margin, y, "Inclusion: Not found yet — check the bulletin board later.")
                c.setFillColorRGB(0, 0, 0)
            y -= 24

            c.setFont("Helvetica-Oblique", 11)
            c.drawString(margin, y, "Use this tracker to verify your entry is posted on the bulletin board.")
            y -= 18
            c.setFont("Helvetica", 12)

        # --- disclaimer ---
        c.setFont("Helvetica-Oblique", 11)
        c.drawString(margin, y, "This receipt contains no voting choices and cannot be used to prove how you voted.")
        y -= 16
        c.drawString(margin, y, "Keep this reference if you need to contact support.")

        c.showPage()
        c.save()

        resp = make_response(buf.getvalue())
        resp.headers["Content-Type"] = "application/pdf"
        safe_id = "".join(ch for ch in election_id if ch.isalnum() or ch in ("-", "_")) or "election"
        resp.headers["Content-Disposition"] = f'attachment; filename="vote_receipt_{safe_id}.pdf"'
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        resp.headers["Referrer-Policy"] = "no-referrer"
        return resp

    # -------- plain-text fallback --------
    lines = [
        f"Vote receipt — {election_name}",
        f"Timestamp: {ts}",
        f"Election ID: {election_id}",
    ]
    if tracker:
        lines.append(f"Tracker: {tracker}")
        lines.append("Use this tracker to verify your entry is posted on the bulletin board.")
    lines.append("This receipt contains no voting choices and cannot be used to prove how you voted.")
    text = "\n".join(lines) + "\n"

    resp = make_response(text)
    resp.headers["Content-Type"] = "text/plain; charset=utf-8"
    safe_id = "".join(ch for ch in election_id if ch.isalnum() or ch in ("-", "_")) or "election"
    resp.headers["Content-Disposition"] = f'attachment; filename="vote_receipt_{safe_id}.txt"'
    return resp
