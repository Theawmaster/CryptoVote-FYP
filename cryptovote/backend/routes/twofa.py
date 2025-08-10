# twofa.py
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Blueprint, request, jsonify, session
import hashlib, pyotp
from models.voter import Voter
from models.db import db

otp_bp = Blueprint('otp', __name__)
otp_cooldown = {}
SGT = ZoneInfo("Asia/Singapore")

@otp_bp.route('/2fa-verify', methods=['POST'])
def verify_2fa():
    data = request.get_json() or {}
    email = data.get('email')                  # you may ignore client email & use session only
    otp = data.get('otp')

    if not otp:
        return jsonify({'error': 'OTP is required'}), 400

    # Require a pending session (set in /admin-login or /login)
    if not session.get('email') or session.get('twofa') is True:
        return jsonify({'error': 'No pending 2FA session'}), 403

    # optional: sanity if client email mismatches session
    if email and hashlib.sha256(email.encode()).hexdigest() != session['email']:
        return jsonify({'error': 'Session/email mismatch'}), 403

    # optional: expire pending stage after N minutes
    started = session.get('twofa_started_at')
    if started:
        try:
            if datetime.now(SGT) - datetime.fromisoformat(started) > timedelta(minutes=5):
                session.clear()
                return jsonify({'error': '2FA challenge expired'}), 403
        except Exception:
            pass

    email_hash = session['email']
    voter = Voter.query.filter_by(email_hash=email_hash).first()
    if not voter:
        return jsonify({'error': 'Unknown user'}), 404

    # Cooldown
    now = datetime.now(tz=SGT)
    last_attempt = otp_cooldown.get(email_hash)
    if last_attempt and (now - last_attempt) < timedelta(seconds=10):
        return jsonify({'error': 'Too many attempts. Please wait.'}), 429

    totp = pyotp.TOTP(voter.totp_secret)
    if not totp.verify(otp):
        otp_cooldown[email_hash] = now
        return jsonify({'error': 'Invalid OTP'}), 401

    # Only here do we mark DB as logged in
    voter.logged_in = True
    voter.logged_in_2fa = True
    voter.last_2fa_at = now
    db.session.commit()

    session['role'] = voter.vote_role
    session['twofa'] = True
    session.modified = True

    return jsonify({'message': '2FA successful. Access granted.', 'role': voter.vote_role}), 200
