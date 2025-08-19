# utilities/logger_utils.py
import hashlib
from datetime import datetime, timezone
from models.admin_log import AdminLog
from models.db import db

GENESIS = "0"*64

def iso_utc(ts): return ts.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def compute_log_hash(prev_hash, email, role, action, ts_iso, ip_address):
    payload = f"{prev_hash}|{email}|{role}|{action}|{ts_iso}|{ip_address}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def log_admin_action(action: str, email: str, role: str, ip_address: str):
    try:
        with db.session.begin():
            last = (db.session.query(AdminLog.entry_hash)
                    .order_by(AdminLog.id.desc())
                    .with_for_update()
                    .first())
            prev_hash = last[0] if last else GENESIS
            ts = datetime.now(timezone.utc).replace(microsecond=0)
            entry_hash = compute_log_hash(prev_hash, email, role, action, iso_utc(ts), ip_address)

            db.session.add(AdminLog(
                admin_email=email, role=role, action=action,
                timestamp=ts, ip_address=ip_address,
                prev_hash=prev_hash, entry_hash=entry_hash
            ))

        # OPTIONAL: soft hook (lazy import avoids cycles)
        try:
            from services.admin_log_auditor import alert_on_chain_breaks
            alert_on_chain_breaks(throttle_seconds=600)
        except Exception as _e:
            # keep logging non-fatal; never break request flow
            pass

    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Failed to write admin log: {e}")
