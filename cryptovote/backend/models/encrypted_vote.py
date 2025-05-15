from models.db import db
from datetime import datetime


class EncryptedVote(db.Model):
    __tablename__ = 'encrypted_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    vote_ciphertext = db.Column(db.Text, nullable=False)
    vote_exponent = db.Column(db.Integer, nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    cast_at = db.Column(db.DateTime, default=datetime.utcnow)