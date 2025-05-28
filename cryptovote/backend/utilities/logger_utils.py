from models.admin_log import AdminLog
from models.db import db
from datetime import datetime

def log_admin_action(action, email, role, ip):
    log = AdminLog(
        admin_email=email,
        role=role,
        action=action,
        ip_address=ip,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()
