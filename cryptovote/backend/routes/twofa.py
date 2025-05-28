from flask import Blueprint, request, jsonify, session
import hashlib, pyotp
from models.voter import Voter
from models.db import db
from datetime import datetime

otp_bp = Blueprint('otp', __name__)
otp_cooldown = {}  # {email_hash: last_failed_attempt_time}

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

    # Cooldown check (10s example)
    from datetime import timedelta
    now = datetime.utcnow()
    last_attempt = otp_cooldown.get(email_hash)
    if last_attempt and (now - last_attempt) < timedelta(seconds=10): # Cooldown is 10 seconds
        return jsonify({'error': 'Too many attempts. Please wait.'}), 429

    totp = pyotp.TOTP(voter.totp_secret)
    if totp.verify(otp):
        voter.vote_status = True
        voter.last_2fa_at = datetime.utcnow()
        
        session["email"] = voter.email_hash
        session["role"] = voter.vote_role
        
        print(f"✅ 2FA success. Set vote_status for {email_hash} at {datetime.utcnow()}") # For Debugging
        print("Session after login:", session)
        
        db.session.commit()
        return jsonify({'message': '2FA successful. Voting access granted.'}), 200
    else:
        otp_cooldown[email_hash] = now
        return jsonify({'error': 'Invalid OTP'}), 401
