from flask import Blueprint, request, jsonify, session
import hashlib, pyotp
from models.voter import Voter
from models.db import db
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+

otp_bp = Blueprint('otp', __name__)
otp_cooldown = {}  # {email_hash: last_failed_attempt_time}

SGT = ZoneInfo("Asia/Singapore")  # UTC+8

@otp_bp.route('/2fa-verify', methods=['POST'])
def verify_2fa():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required'}), 400

    email_hash = hashlib.sha256(email.encode()).hexdigest()
    voter = Voter.query.filter_by(email_hash=email_hash).first()

    if not voter or not voter.logged_in:
        return jsonify({'error': 'User is not logged in'}), 403
    
    if voter.logged_in_2fa and voter.last_2fa_at:
        last_2fa_time = voter.last_2fa_at.astimezone(SGT)
        now = datetime.now(tz=SGT)
        if (now - last_2fa_time) < timedelta(minutes=5):
            return jsonify({'error': 'Already logged in with 2FA. Please wait before re-verifying.'}), 403

    # Cooldown check (10s example)
    now = datetime.now(tz=SGT)
    last_attempt = otp_cooldown.get(email_hash)
    if last_attempt and (now - last_attempt) < timedelta(seconds=10):
        return jsonify({'error': 'Too many attempts. Please wait.'}), 429

    totp = pyotp.TOTP(voter.totp_secret)
    if totp.verify(otp):
        voter.logged_in_2fa = True
        voter.last_2fa_at = now

        session["email"] = voter.email_hash
        session["role"] = voter.vote_role

        print(f"✅ 2FA success. Set vote_status for {email_hash} at {now}")  # For Debugging
        print("Session after login:", session)

        db.session.commit()
        return jsonify({'message': '2FA successful. Access granted.'}), 200
    else:
        otp_cooldown[email_hash] = now
        return jsonify({'error': 'Invalid OTP'}), 401
