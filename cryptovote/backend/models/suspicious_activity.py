from models.db import db
from datetime import datetime
from _zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

class SuspiciousActivity(db.Model):
    __tablename__ = "suspicious_activity"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=True)
    ip_address = db.Column(db.String, nullable=False)
    reason = db.Column(db.String, nullable=False)
    route_accessed = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(SGT))
