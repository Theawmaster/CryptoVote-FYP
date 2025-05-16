from models.db import db
from datetime import datetime

class IssuedToken(db.Model):
    __tablename__ = 'issued_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)

