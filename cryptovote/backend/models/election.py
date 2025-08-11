from models.db import db
from datetime import datetime

class Election(db.Model):
    __tablename__ = 'elections'

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    has_started = db.Column(db.Boolean, default=False)
    has_ended = db.Column(db.Boolean, default=False)
    tally_generated = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())
    
    candidates = db.relationship(
        'Candidate',
        back_populates='election',
        cascade='all, delete-orphan',
        passive_deletes=True
    )


class Candidate(db.Model):
    __tablename__ = 'candidates'

    id = db.Column(db.String(64), primary_key=True)  # or Integer/UUID
    name = db.Column(db.String(128), nullable=False)

    election_id = db.Column(
        db.String(64),
        db.ForeignKey('elections.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    election = db.relationship('Election', back_populates='candidates')

    votes = db.relationship(
        'EncryptedCandidateVote',
        back_populates='candidate',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
