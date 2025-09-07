# models/wbb_entry.py
from models.db import db
from sqlalchemy import UniqueConstraint
from datetime import datetime
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

class WbbEntry(db.Model):
    __tablename__ = "wbb_entries"

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.String(128), index=True, nullable=False)
    tracker     = db.Column(db.String(64),  index=True, nullable=False)   # hex, shown to voter
    token_hash  = db.Column(db.String(64),  index=True, nullable=False)   # sha256(token) hex
    position    = db.Column(db.Integer, nullable=False)                   # append order (0-based)
    leaf_hash   = db.Column(db.String(64),  nullable=False)               # sha256(leaf_input) hex
    created_at  = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(SGT))
    commitment_hash = db.Column(db.String(64), nullable=True)  # new

    __table_args__ = (
        UniqueConstraint('election_id', 'token_hash', name='uq_wbb_eid_tokenhash'),
        UniqueConstraint('election_id', 'position',   name='uq_wbb_eid_pos'),
    )
