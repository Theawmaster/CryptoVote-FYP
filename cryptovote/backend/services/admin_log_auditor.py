a# services/admin_log_auditor.py
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from models.db import db
from utilities.email_utils import send_email
try:
    from services.anomaly_utils import flag_suspicious_activity
except Exception:
    flag_suspicious_activity = None

GENESIS = "0"*64
_SCAN_SQL = text("""
WITH chain AS (
  SELECT id, prev_hash, entry_hash,
         LAG(entry_hash) OVER (ORDER BY id) AS expected_prev
  FROM admin_logs
)
SELECT id, prev_hash, entry_hash, expected_prev
FROM chain
WHERE COALESCE(prev_hash, :genesis) IS DISTINCT FROM COALESCE(expected_prev, :genesis)
ORDER BY id ASC
""")

def find_breaks():
    return [dict(r) for r in db.session.execute(_SCAN_SQL, {"genesis": GENESIS}).mappings().all()]

_last_alert_at: datetime | None = None

def alert_on_chain_breaks(throttle_seconds: int = 600) -> bool:
    """Send one email if any break exists; throttled to avoid spam."""
    global _last_alert_at
    now = datetime.now(timezone.utc)
    if _last_alert_at and (now - _last_alert_at) < timedelta(seconds=throttle_seconds):
        return False

    breaks = find_breaks()
    if not breaks:
        return False

    lines = [
        "Admin Log Chain Integrity Alert",
        f"Detected {len(breaks)} break(s) at {now.isoformat().replace('+00:00','Z')}.",
        "",
        "First discrepancies:"
    ] + [
        f"- id={b['id']} prev={b['prev_hash']} expected_prev={b['expected_prev']}"
        for b in breaks[:10]
    ]

    sent = send_email("🚨 Admin Log Chain Break Detected", "\n".join(lines))

    if flag_suspicious_activity:
        try:
            flag_suspicious_activity(email=None, ip_address="127.0.0.1",
                                     reason="ADMIN_LOG_CHAIN_MISMATCH",
                                     route_accessed="/internal/chain-audit")
        except Exception as e:
            print(f"⚠️ SuspiciousActivity flag failed: {e}")

    if sent:
        _last_alert_at = now
    return sent
