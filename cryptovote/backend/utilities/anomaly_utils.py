from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from models.suspicious_activity import SuspiciousActivity
from models.db import db

SGT = ZoneInfo("Asia/Singapore")

FAILED_LOGIN = "FAILED_LOGIN"  # one canonical reason string

def now_sgt():
    return datetime.now(SGT)

def flag_suspicious_activity(email, ip_address, reason, route_accessed, *, details=None, severity="medium"):
    """Insert one suspicious activity row."""
    try:
        new_flag = SuspiciousActivity(
            email=email,
            ip_address=ip_address,
            reason=reason,
            route_accessed=route_accessed,
            timestamp=now_sgt(),           # keep SGT to match current storage
            # if your model has these fields, include them:
            # details=details or {},
            # severity=severity,
        )
        db.session.add(new_flag)
        db.session.commit()
        return new_flag.id
    except Exception as e:
        db.session.rollback()
        print(f"[⚠️ Suspicious Activity Logging Failed] {e}")
        return None

def failed_logins_last_10min(ip: str) -> int:
    """Count failed logins from this IP in the last 10 minutes."""
    ten_min_ago = now_sgt() - timedelta(minutes=10)   # ✅ was 'utnow' typo
    return (SuspiciousActivity.query
            .filter(
                SuspiciousActivity.ip_address == ip,
                SuspiciousActivity.reason == FAILED_LOGIN,   # ✅ exact match
                SuspiciousActivity.timestamp >= ten_min_ago
            )
            .count())

def too_many_failed_logins(ip: str, threshold: int = 5) -> bool:
    """Convenience gate for rate-limiting/auth throttling."""
    return failed_logins_last_10min(ip) >= threshold

