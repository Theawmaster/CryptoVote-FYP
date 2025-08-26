# models/candidate_tally.py
from models.db import db
from datetime import datetime
from zoneinfo import ZoneInfo
SGT = ZoneInfo("Asia/Singapore")

class CandidateTally(db.Model):
    __tablename__ = "candidate_tallies"

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.String(64), db.ForeignKey("elections.id"), index=True, nullable=False)
    candidate_id = db.Column(db.String(64), db.ForeignKey("candidates.id"), index=True, nullable=False)
    total = db.Column(db.Integer, nullable=False, default=0)
    computed_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(SGT), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("election_id", "candidate_id", name="uq_tally_per_candidate"),
    )
