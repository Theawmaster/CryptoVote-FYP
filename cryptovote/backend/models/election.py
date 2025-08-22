# models/election.py
from models.db import db
from datetime import timezone, datetime
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

class Election(db.Model):
    __tablename__ = "elections"

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(128), nullable=False)

    # NEW: which RSA key this election uses
    rsa_key_id = db.Column(db.String(128), nullable=True, index=True)  # make non-null later

    # make all datetimes tz-aware
    start_time  = db.Column(db.DateTime(timezone=True), nullable=True)
    end_time    = db.Column(db.DateTime(timezone=True), nullable=True)

    is_active   = db.Column(db.Boolean, default=False)
    has_started = db.Column(db.Boolean, default=False)
    has_ended   = db.Column(db.Boolean, default=False)
    tally_generated = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    candidates = db.relationship(
        "Candidate",
        back_populates="election",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(128), nullable=False)

    election_id = db.Column(
        db.String(64),
        db.ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    election = db.relationship("Election", back_populates="candidates")
    votes = db.relationship(
        "EncryptedCandidateVote",
        back_populates="candidate",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
