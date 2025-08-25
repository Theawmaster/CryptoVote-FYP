from models.db import db
from datetime import datetime
from models.election import Election
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

class EncryptedCandidateVote(db.Model):
    __tablename__ = 'encrypted_candidate_votes'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.String(64),
        db.ForeignKey('candidates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    vote_ciphertext = db.Column(db.Text, nullable=False)
    vote_exponent = db.Column(db.Integer, nullable=False)
    token_hash = db.Column(db.String(64), nullable=False)
    cast_at = db.Column(db.DateTime, default=datetime.now(SGT))
    election_id = db.Column(db.String(64), db.ForeignKey("elections.id"), index=True)

    candidate = db.relationship('Candidate', back_populates='votes')