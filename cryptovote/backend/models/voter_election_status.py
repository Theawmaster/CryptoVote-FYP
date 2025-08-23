# models/voter_election_status.py
from models.db import db

class VoterElectionStatus(db.Model):
    __tablename__ = "voter_election_status"

    id          = db.Column(db.Integer, primary_key=True)
    voter_id    = db.Column(db.Integer, db.ForeignKey("voter.id"), index=True, nullable=False)
    election_id = db.Column(db.String,  db.ForeignKey("elections.id"), index=True, nullable=False)

    token_issued_at = db.Column(db.DateTime, nullable=True)  # set when blind-sign succeeds
    voted_at        = db.Column(db.DateTime, nullable=True)  # optional, set when cast-vote succeeds

    __table_args__ = (
        db.UniqueConstraint("voter_id", "election_id", name="uq_voter_election"),
    )