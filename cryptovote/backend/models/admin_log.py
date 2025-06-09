# models/admin_log.py

from models.db import db

class AdminLog(db.Model):
    __tablename__ = 'admin_logs'

    id = db.Column(db.Integer, primary_key=True)
    admin_email = db.Column(db.String(120))
    role = db.Column(db.String(20))
    action = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))
    
    prev_hash = db.Column(db.String(64))
    entry_hash = db.Column(db.String(64))
