# routes/receipt.py
import os
from flask import Blueprint, request, make_response
from datetime import datetime
from _zoneinfo import ZoneInfo
import secrets

SGT = ZoneInfo("Asia/Singapore")
receipt_bp = Blueprint("receipt", __name__)

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
def vote_receipt():
    election_name = request.args.get("election_name", "Election")
    ts = datetime.now(SGT).strftime("%d %b %Y, %H:%M %Z")
    support_ref = secrets.token_hex(6)

    if HAVE_PDF:
        from io import BytesIO
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setTitle(f"Vote receipt — {election_name}")

        page_w, page_h = letter
        margin = 56
        y = page_h - margin

        # --- logos ---
        ntu_logo = _asset_path("ntu_logo.png")
        crypto_logo = _asset_path("cryptovote_logo.png")

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

        draw_logo(ntu_logo, margin, y)
        draw_logo(crypto_logo, page_w - margin - 80, y)
        y -= 60

        # --- title ---
        c.setFont("Helvetica-Bold", 16)
        title = f"{election_name} — Vote received"
        title_w = c.stringWidth(title, "Helvetica-Bold", 16)
        c.drawString((page_w - title_w) / 2, y, title)
        y -= 30

        # --- body ---
        c.setFont("Helvetica", 12)
        c.drawString(margin, y, f"Timestamp: {ts}"); y -= 18
        c.drawString(margin, y, f"Support Ref: {support_ref}"); y -= 24

        c.setFont("Helvetica-Oblique", 11)
        c.drawString(margin, y, "This receipt contains no voting choices and cannot be used to prove how you voted."); y -= 18
        c.drawString(margin, y, "Keep this reference if you need to contact support."); y -= 18

        c.showPage()
        c.save()

        pdf_bytes = buf.getvalue()
        buf.close()

        resp = make_response(pdf_bytes)
        resp.headers["Content-Type"] = "application/pdf"
        resp.headers["Content-Disposition"] = f'attachment; filename="vote_receipt_{support_ref}.pdf"'
        return resp

    # fallback plain text
    text = (
        f"Vote receipt — {election_name}\n"
        f"Timestamp: {ts}\n"
        f"Support Ref: {support_ref}\n"
        f"This receipt contains no voting choices and cannot be used to prove how you voted.\n"
    )
    resp = make_response(text)
    resp.headers["Content-Type"] = "text/plain; charset=utf-8"
    resp.headers["Content-Disposition"] = f'attachment; filename="vote_receipt_{support_ref}.txt"'
    return resp
