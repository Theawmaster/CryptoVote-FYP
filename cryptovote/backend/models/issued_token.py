from models.db import db
from datetime import datetime
from _zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

class IssuedToken(db.Model):
    __tablename__ = 'issued_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.now(tz=SGT))
    used = db.Column(db.Boolean, default=False)

