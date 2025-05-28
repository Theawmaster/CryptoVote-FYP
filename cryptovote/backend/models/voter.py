from models.db import db

class Voter(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    email_hash = db.Column(db.String(64), unique=True, nullable=False)
    vote_role = db.Column(db.String(20), default='voter')  # 'admin', 'auditor', 'voter'
    public_key = db.Column(db.Text, nullable=True)
    verification_token = db.Column(db.String(128), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    logged_in = db.Column(db.Boolean, default=False)
    totp_secret = db.Column(db.String(64), nullable=True)  # extended from 16 to 64 if needed
    last_login_ip = db.Column(db.String(45), nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_2fa_at = db.Column(db.DateTime, nullable=True)
    vote_status = db.Column(db.Boolean, default=False)
    has_token = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
