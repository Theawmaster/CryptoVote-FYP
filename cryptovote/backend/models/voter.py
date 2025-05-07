from models.db import db

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_hash = db.Column(db.String(64), unique=True, nullable=False)
    public_key = db.Column(db.Text, nullable=True)
    verification_token = db.Column(db.String(128), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    totp_secret = db.Column(db.String(16), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())