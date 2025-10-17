# routes/admin/security_routes.py
from flask import Blueprint, request, jsonify, Response, send_file, current_app
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from io import BytesIO
from fpdf import FPDF

from sqlalchemy import func
from utilities.auth_utils import role_required
from utilities.pii_utils import email_hmac
from models.db import db
from models.suspicious_activity import SuspiciousActivity

SGT = ZoneInfo("Asia/Singapore")
bp  = Blueprint("security", __name__)

# ---------- time helpers ----------
def to_sgt(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=SGT)
    return dt.astimezone(SGT)

def _parse_iso8601(s: str | None):
    if not s:
        return None
    s = s.strip().replace("Z", "+00:00")
    # tolerate "YYYY-mm-dd HH:MM:SS +08:00" → "YYYY-mm-dd HH:MM:SS+08:00"
    if len(s) >= 6 and s[-6] == " " and s[-3] == ":" and s[-5:-3].isdigit() and s[-2:].isdigit():
        s = s[:-6] + "+" + s[-5:]
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def _to_naive_sgt(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(SGT).replace(tzinfo=None)
    return dt

def _norm_to_naive_sgt(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(SGT).replace(tzinfo=None)
    return dt

# ---------- routes ----------

@bp.route("/security/suspicious", methods=["GET"])
@role_required("admin")
def list_suspicious():
    """
    List suspicious_activity (paged + filters)

    Query params:
      limit (<=200), offset
      email_hash (preferred), email (deprecated; server hashes to match), ip, reason (substring)
      since (ISO8601), until (ISO8601), since_minutes (int)
      sort: id|timestamp|reason  (default: timestamp)
      order: asc|desc (default: desc)
    """
    limit  = max(1, min(int(request.args.get("limit", 50)), 200))
    offset = max(0, int(request.args.get("offset", 0)))

    q_base = SuspiciousActivity.query

    # ---- filters ----
    email_hash = request.args.get("email_hash")
    if email_hash:
        q_base = q_base.filter(SuspiciousActivity.email_hash == email_hash)

    email_plain = request.args.get("email")  # back-compat; convert to hash
    if (not email_hash) and email_plain:
        q_base = q_base.filter(SuspiciousActivity.email_hash == email_hmac(email_plain))

    ip = request.args.get("ip")
    if ip:
        q_base = q_base.filter(SuspiciousActivity.ip_address == ip)

    reason = request.args.get("reason")
    if reason:
        q_base = q_base.filter(SuspiciousActivity.reason.ilike(f"%{reason}%"))

    # time window (normalize to naive SGT)
    since = _to_naive_sgt(_parse_iso8601(request.args.get("since")))
    until = _to_naive_sgt(_parse_iso8601(request.args.get("until")))
    if not since and (m := request.args.get("since_minutes")):
        try:
            since = _to_naive_sgt(datetime.now(SGT) - timedelta(minutes=int(m)))
        except Exception:
            since = None

    q_db = q_base
    if since:
        q_db = q_db.filter(SuspiciousActivity.timestamp >= since)
    if until:
        q_db = q_db.filter(SuspiciousActivity.timestamp <= until)

    # sort
    sort_field = {
        "id": SuspiciousActivity.id,
        "timestamp": SuspiciousActivity.timestamp,
        "reason": SuspiciousActivity.reason,
    }.get(request.args.get("sort", "timestamp"), SuspiciousActivity.timestamp)
    order = request.args.get("order", "desc")
    q_db = q_db.order_by(sort_field.desc() if order == "desc" else sort_field.asc())

    # pagination + totals
    if since or until:
        # in-Python defensive re-filter to respect timezone normalization
        q_base_sorted = q_base.order_by(sort_field.desc() if order == "desc" else sort_field.asc())
        rows_all = q_base_sorted.all()

        def _in_window(rts: datetime | None) -> bool:
            ndt = _norm_to_naive_sgt(rts)
            if ndt is None:
                return False
            if since and ndt < since:
                return False
            if until and ndt > until:
                return False
            return True

        filtered = [r for r in rows_all if _in_window(getattr(r, "timestamp", None))]
        total = len(filtered)
        rows = filtered[offset : offset + limit]
    else:
        # IMPORTANT: count only by scalar column to avoid selecting unmapped fields
        total = (db.session.query(func.count())
                 .select_from(q_db.subquery())
                 .scalar())
        rows  = q_db.limit(limit).offset(offset).all()

    def to_dict(r: SuspiciousActivity):
        return {
            "id": r.id,
            "email_hash": r.email_hash,   # privacy-safe; DO NOT expose plaintext email
            "ip_address": r.ip_address,
            "reason": r.reason,
            "route_accessed": r.route_accessed,
            "timestamp": (to_sgt(r.timestamp).isoformat() if r.timestamp else None),
        }

    return jsonify({
        "items": [to_dict(r) for r in rows],
        "total": int(total),
        "limit": limit,
        "offset": offset,
    }), 200


@bp.get("/security/suspicious/count")
@role_required("admin")
def suspicious_count():
    # last 24h in SGT, normalized to naive SGT to match DB values
    since = _to_naive_sgt(datetime.now(SGT) - timedelta(hours=24))
    count = (db.session.query(func.count(SuspiciousActivity.id))
             .filter(SuspiciousActivity.timestamp >= since)
             .scalar())
    return jsonify({"count": int(count)}), 200


@bp.get("/security/suspicious.csv")
@role_required("admin")
def export_suspicious_csv():
    q = SuspiciousActivity.query.order_by(SuspiciousActivity.timestamp.desc())
    rows = q.limit(5000).all()

    def esc(x):
        s = "" if x is None else str(x)
        return "'" + s if s[:1] in ("=", "+", "-", "@") else s

    lines = ["id,email_hash,ip_address,reason,route_accessed,timestamp"]
    for r in rows:
        ts = to_sgt(r.timestamp)
        lines.append(",".join([
            str(r.id),
            esc(r.email_hash or ""),
            r.ip_address,
            esc(r.reason),
            esc(r.route_accessed),
            (ts.isoformat() if ts else "")
        ]))
    csv_data = "\n".join(lines)
    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=suspicious.csv"},
    )


@bp.get("/security/suspicious.pdf")
@role_required("admin")
def export_suspicious_pdf():
    limit  = max(1, min(int(request.args.get("limit", 500)), 5000))
    offset = max(0, int(request.args.get("offset", 0)))

    q = SuspiciousActivity.query

    # filter by email_hash (and back-compat for email param)
    email_hash = request.args.get("email_hash")
    if email_hash:
        q = q.filter(SuspiciousActivity.email_hash == email_hash)
    else:
        email_plain = request.args.get("email")
        if email_plain:
            q = q.filter(SuspiciousActivity.email_hash == email_hmac(email_plain))

    ip = request.args.get("ip")
    if ip:
        q = q.filter(SuspiciousActivity.ip_address == ip)
    reason = request.args.get("reason")
    if reason:
        q = q.filter(SuspiciousActivity.reason.ilike(f"%{reason}%"))

    since = _to_naive_sgt(_parse_iso8601(request.args.get("since")))
    until = _to_naive_sgt(_parse_iso8601(request.args.get("until")))
    if not since and (m := request.args.get("since_minutes")):
        try:
            since = _to_naive_sgt(datetime.now(SGT) - timedelta(minutes=int(m)))
        except Exception:
            since = None
    if since:
        q = q.filter(SuspiciousActivity.timestamp >= since)
    if until:
        q = q.filter(SuspiciousActivity.timestamp <= until)

    rows = (q.order_by(SuspiciousActivity.timestamp.desc())
              .limit(limit).offset(offset).all())

    # ---- build PDF ----
    pdf = FPDF()
    try:
        if current_app and current_app.config.get("TESTING"):
            pdf.set_compression(False)
    except Exception:
        pass

    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title & meta
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Suspicious Activity Report", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    now_sgt = datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(0, 7, f"Generated: {now_sgt} SGT", ln=True)
    pdf.cell(0, 7, f"Total rows: {len(rows)} (limit {limit}, offset {offset})", ln=True)
    pdf.ln(3)

    headers = ["ID", "Email Hash", "IP", "Reason", "Route", "Timestamp"]
    widths  = [14, 40, 28, 36, 50, 32]
    pdf.set_font("Arial", "B", 10)
    for h, w in zip(headers, widths):
        pdf.cell(w, 8, h, border=1)
    pdf.ln(8)

    def trunc(s: str | None, n: int) -> str:
        s = "" if s is None else str(s)
        return (s[: n - 3] + "...") if len(s) > n else s  # ASCII

    def latin1_safe(s: str) -> str:
        return ("" if s is None else str(s)).encode("latin-1", "ignore").decode("latin-1")

    pdf.set_font("Arial", "", 9)
    for r in rows:
        ts = ""
        if getattr(r, "timestamp", None):
            ts_dt = to_sgt(r.timestamp)
            ts = ts_dt.strftime("%Y-%m-%d %H:%M:%S %Z")

        cells = [
                str(r.id),
                trunc(r.email_hash, 32) if r.email_hash else "",
                trunc(r.ip_address, 24),
                trunc(r.reason, 30),
                trunc(r.route_accessed, 44),
                trunc(ts, 28),
            ]
        for text, w in zip(cells, widths):
            pdf.cell(w, 7, latin1_safe(text), border=1)
        pdf.ln(7)

    pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace") 
    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="suspicious.pdf",
        mimetype="application/pdf",
    )

# ---------- end routes ----------


# Quick Smoke Test
# curl -s "http://localhost:5010/admin/security/suspicious?limit=20" | jq .

# # only last 10 minutes
# curl -s "http://localhost:5010/admin/security/suspicious?since_minutes=10" | jq .

# # count for a header badge (last 24h default)
# curl -s "http://localhost:5010/admin/security/suspicious/count" | jq .

# # CSV dump
# curl -s -D- "http://localhost:5010/admin/security/suspicious.csv" | head

# # PDF dump
# curl -s -D- "http://localhost:5010/admin/security/suspicious.pdf" | head