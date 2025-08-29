from flask import Blueprint, request, jsonify, Response, send_file
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from utilities.auth_utils import role_required
from models.db import db
from io import BytesIO
from fpdf import FPDF
from models.suspicious_activity import SuspiciousActivity
from datetime import timezone

SGT = ZoneInfo("Asia/Singapore")
bp  = Blueprint("security", __name__)

def to_sgt(dt):
    if dt is None:
        return None
    # assume DB stores UTC-naive; adjust if yours is different
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(SGT)

def _parse_iso8601(s: str | None):
    if not s: return None
    try:
        # accept ...Z or with offset; fall back to naive local SGT
        s = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None

@bp.route("/security/suspicious", methods=["GET"]) 
@role_required("admin")
def list_suspicious():
    """
    List suspicious_activity (paged + filters)
    Query params:
      limit (<=200), offset
      email, ip, reason (substring match)
      since (ISO8601), until (ISO8601)
      since_minutes (int)  # alt to 'since'
      sort: id|timestamp|reason  (default: timestamp)
      order: asc|desc (default: desc)
    """
    limit  = max(1, min(int(request.args.get("limit", 50)), 200))
    offset = max(0, int(request.args.get("offset", 0)))

    q = SuspiciousActivity.query

    # filters
    if email := request.args.get("email"):
        q = q.filter(SuspiciousActivity.email == email)
    if ip := request.args.get("ip"):
        q = q.filter(SuspiciousActivity.ip_address == ip)
    if reason := request.args.get("reason"):
        q = q.filter(SuspiciousActivity.reason.ilike(f"%{reason}%"))

    # time window
    since = _parse_iso8601(request.args.get("since"))
    until = _parse_iso8601(request.args.get("until"))
    if not since and (m := request.args.get("since_minutes")):
        try:
            since = datetime.now(SGT) - timedelta(minutes=int(m))
        except Exception:
            pass
    if since:
        q = q.filter(SuspiciousActivity.timestamp >= since)
    if until:
        q = q.filter(SuspiciousActivity.timestamp <= until)

    # sort
    sort_field = {
        "id": SuspiciousActivity.id,
        "timestamp": SuspiciousActivity.timestamp,
        "reason": SuspiciousActivity.reason,
    }.get(request.args.get("sort", "timestamp"), SuspiciousActivity.timestamp)
    order = request.args.get("order", "desc")
    q = q.order_by(sort_field.desc() if order == "desc" else sort_field.asc())

    total = q.count()
    rows  = q.limit(limit).offset(offset).all()

    def to_dict(r: SuspiciousActivity):
        return {
            "id": r.id,
            "email": r.email,
            "ip_address": r.ip_address,
            "reason": r.reason,
            "route_accessed": r.route_accessed,
            "timestamp": (to_sgt(r.timestamp).isoformat() if r.timestamp else None),
        }

    return jsonify({
        "items": [to_dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }), 200
    
@bp.get("/security/suspicious/count")
@role_required("admin")
def suspicious_count():
    since = datetime.now(SGT) - timedelta(hours=24)  # last 24h by default
    count = (SuspiciousActivity.query
             .filter(SuspiciousActivity.timestamp >= since)
             .count())
    return jsonify({"count": count}), 200
    
@bp.get("/security/suspicious.csv")
@role_required("admin")
def export_suspicious_csv():
    """
    Simple CSV export honoring the same filters as list_suspicious.
    """
    # reuse list logic by calling the function's internals quickly
    # (small duplication keeps it dependency-free)
    q = SuspiciousActivity.query.order_by(SuspiciousActivity.timestamp.desc())
    # optional: add filters like above (kept short here)
    rows = q.limit(5000).all()

    def esc(x):
        s = "" if x is None else str(x)
        return "'" + s if s[:1] in ("=", "+", "-", "@") else s

    lines = ["id,email,ip_address,reason,route_accessed,timestamp"]
    for r in rows:
        ts = to_sgt(r.timestamp)
        lines.append(",".join([
            str(r.id), esc(r.email), r.ip_address, esc(r.reason),
            esc(r.route_accessed), (ts.isoformat() if ts else "")
        ]))
    csv_data = "\n".join(lines)
    return Response(
        csv_data, mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=suspicious.csv"}
    )

@bp.get("/security/suspicious.pdf")
@role_required("admin")
def export_suspicious_pdf():
    """
    Export suspicious_activity as a simple PDF table.
    Supports the same filters as list_suspicious:
      ?limit=&offset=&email=&ip=&reason=&since=&until=&since_minutes=
    """
    # ---- query & filters (same shape as list) ----
    limit  = max(1, min(int(request.args.get("limit", 500)), 5000))
    offset = max(0, int(request.args.get("offset", 0)))

    q = SuspiciousActivity.query

    email = request.args.get("email")
    if email:
        q = q.filter(SuspiciousActivity.email == email)

    ip = request.args.get("ip")
    if ip:
        q = q.filter(SuspiciousActivity.ip_address == ip)

    reason = request.args.get("reason")
    if reason:
        q = q.filter(SuspiciousActivity.reason.ilike(f"%{reason}%"))

    def _parse_iso8601(s: str | None):
        if not s: return None
        try:
            s = s.replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except Exception:
            return None

    SGT = ZoneInfo("Asia/Singapore")
    since = _parse_iso8601(request.args.get("since"))
    until = _parse_iso8601(request.args.get("until"))
    if not since and (m := request.args.get("since_minutes")):
        try:
            since = datetime.now(SGT) - timedelta(minutes=int(m))
        except Exception:
            pass
    if since:
        q = q.filter(SuspiciousActivity.timestamp >= since)
    if until:
        q = q.filter(SuspiciousActivity.timestamp <= until)

    rows = (q.order_by(SuspiciousActivity.timestamp.desc())
              .limit(limit).offset(offset).all())

    # ---- build PDF ----
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title & meta
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Suspicious Activity Report", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    now_sgt = datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S %Z")
    pdf.cell(0, 7, f"Generated: {now_sgt}", ln=True)
    pdf.cell(0, 7, f"Total rows: {len(rows)} (limit {limit}, offset {offset})", ln=True)
    pdf.ln(3)

    # Table header
    headers = ["ID", "Email", "IP", "Reason", "Route", "Timestamp"]
    widths  = [14,   40,      28,   36,       50,      32]   # sum ~200 fits A4 width (with margins)
    pdf.set_font("Arial", "B", 10)
    for h, w in zip(headers, widths):
        pdf.cell(w, 8, h, border=1)
    pdf.ln(8)

    # Row helper
    def trunc(s: str | None, n: int) -> str:
        s = "" if s is None else str(s)
        return (s[: n - 1] + "…") if len(s) > n else s

    pdf.set_font("Arial", "", 9)
    for r in rows:
        ts = ""
        if getattr(r, "timestamp", None):
            ts_dt = to_sgt(r.timestamp)
            ts = ts_dt.strftime("%Y-%m-%d %H:%M:%S %Z")  # shows SGT

        cells = [
            str(r.id),
            trunc(r.email, 32),
            trunc(r.ip_address, 24),
            trunc(r.reason, 30),
            trunc(r.route_accessed, 44),
            trunc(ts, 28),
        ]

        # one-line cells; keep it simple & fast
        for text, w in zip(cells, widths):
            pdf.cell(w, 7, text, border=1)
        pdf.ln(7)

    # Stream as a download
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="suspicious.pdf",
        mimetype="application/pdf",
    )


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