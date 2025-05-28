from models.db import db
from datetime import datetime

class Election(db.Model):
    __tablename__ = 'elections'

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    has_started = db.Column(db.Boolean, default=False)
    has_ended = db.Column(db.Boolean, default=False)
    tally_generated = db.Column(db.Boolean, default=False)
