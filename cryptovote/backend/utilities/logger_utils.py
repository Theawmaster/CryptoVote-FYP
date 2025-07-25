import hashlib
from models.admin_log import AdminLog
from models.db import db
from datetime import datetime
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

def get_last_log_hash():
    last_entry = AdminLog.query.order_by(AdminLog.id.desc()).first()
    return last_entry.entry_hash if last_entry else '0' * 64

def compute_log_hash(prev_hash, email, role, action, timestamp, ip_address):
    log_str = f"{prev_hash}|{email}|{role}|{action}|{timestamp}|{ip_address}"
    return hashlib.sha256(log_str.encode()).hexdigest()

def log_admin_action(action, email, role, ip_address):
    try:
        prev_hash = get_last_log_hash()
        timestamp = datetime.now(SGT)
        entry_hash = compute_log_hash(prev_hash, email, role, action, timestamp, ip_address)

        new_log = AdminLog(
            admin_email=email,
            role=role,
            action=action,
            timestamp=timestamp,
            ip_address=ip_address,
            prev_hash=prev_hash,
            entry_hash=entry_hash
        )

        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Failed to write admin log: {e}")
