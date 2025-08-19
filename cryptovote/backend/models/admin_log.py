# models/admin_log.py
from models.db import db
from sqlalchemy import text
from sqlalchemy.sql import func

GENESIS = "0" * 64

class AdminLog(db.Model):
    __tablename__ = "admin_logs"

    id = db.Column(db.BigInteger, primary_key=True)  # monotonic, sortable
    admin_email = db.Column(db.String(120), nullable=False, index=True)
    role = db.Column(db.String(32), nullable=False, index=True)
    action = db.Column(db.Text, nullable=False)

    # Store UTC with tz. Let DB default to UTC now() as a backstop.
    timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=text("timezone('UTC', now())"),
        index=True,
    )

    ip_address = db.Column(db.String(45), nullable=False)  # IPv4/IPv6 textual

    prev_hash  = db.Column(db.String(64), nullable=False, index=True)
    entry_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)

    __table_args__ = (
        db.CheckConstraint("entry_hash ~ '^[0-9a-f]{64}$'", name="chk_entry_hash_hex"),
        db.CheckConstraint("prev_hash  ~ '^[0-9a-f]{64}$'", name="chk_prev_hash_hex"),
    )
