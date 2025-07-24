from models.suspicious_activity import SuspiciousActivity
from models.db import db
from datetime import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

def flag_suspicious_activity(email, ip_address, reason, route_accessed):
    try:
        new_flag = SuspiciousActivity(
            email=email,
            ip_address=ip_address,
            reason=reason,
            route_accessed=route_accessed,
            timestamp=datetime.now(SGT)
        )
        db.session.add(new_flag)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[⚠️ Suspicious Activity Logging Failed] {e}")

def failed_logins_last_10min(ip):
    ten_min_ago = datetime.utcnow() - timedelta(minutes=10)
    count = SuspiciousActivity.query.filter(
        SuspiciousActivity.ip_address == ip,
        SuspiciousActivity.reason.ilike("%Failed login%"),
        SuspiciousActivity.timestamp >= ten_min_ago
    ).count()
    return count