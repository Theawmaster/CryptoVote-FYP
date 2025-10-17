# models/encrypted_candidate_vote.py
from models.db import db
from datetime import datetime
from zoneinfo import ZoneInfo


SGT = ZoneInfo("Asia/Singapore")

class EncryptedCandidateVote(db.Model):
    __tablename__ = 'encrypted_candidate_votes'

    id = db.Column(db.Integer, primary_key=True)

    # Which candidate this ciphertext contributes to
    candidate_id = db.Column(
        db.String(64),
        db.ForeignKey('candidates.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    # Paillier ciphertext (as base-10 string)
    vote_ciphertext = db.Column(db.Text, nullable=False)

    # Exponent used by phe.EncryptedNumber (0 for client-side 0/1 encoding)
    vote_exponent = db.Column(db.Integer, nullable=False, default=0)

    # Scoped anti-reuse: sha256(f"{election_id}|{token}")
    token_hash = db.Column(db.String(64), nullable=False)

    # Audit timestamps
    cast_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(SGT), nullable=False)

    # Redundant but handy for audit/tally filters
    election_id = db.Column(db.String(64), db.ForeignKey("elections.id"), index=True, nullable=False)

    # ORM backref (keep the name your Candidate model expects)
    candidate = db.relationship('Candidate', back_populates='votes')

    __table_args__ = (
        # one token_hash per election_id
        db.UniqueConstraint('election_id', 'token_hash', name='uq_encvote_eid_tokenhash'),
        # speed up “sum by candidate within election”
        db.Index('ix_encvote_eid_cid', 'election_id', 'candidate_id'),
    )
