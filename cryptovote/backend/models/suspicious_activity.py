# models/suspicious_activity.py
from models.db import db
from datetime import datetime
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

class SuspiciousActivity(db.Model):
    __tablename__ = "suspicious_activity"

    id = db.Column(db.Integer, primary_key=True)

    # Privacy-safe identifier for correlation
    email_hash = db.Column(db.String, nullable=True, index=True)

    # NOTE: Plain 'email' has been removed from the model to match DB and avoid drift.

    ip_address     = db.Column(db.String, nullable=False, index=True)
    reason         = db.Column(db.String, nullable=False)
    route_accessed = db.Column(db.String, nullable=False)
    # Naive SGT timestamp (kept to match existing rows/logic)
    timestamp      = db.Column(db.DateTime, default=lambda: datetime.now(SGT), index=True)
