# twofa.py
from extensions import limiter
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Blueprint, request, jsonify, session, current_app   # ← add current_app
import hashlib, pyotp
from models.voter import Voter
from models.db import db
from time import time

otp_bp = Blueprint('otp', __name__)
# cooldown now keyed by (email_hash, ip)
otp_cooldown = {}  # dict[tuple[str, str], datetime]
SGT = ZoneInfo("Asia/Singapore")

@otp_bp.route('/2fa-verify', methods=['POST'])
@limiter.limit("3 per second; 30 per minute")
def verify_2fa():
    data = request.get_json() or {}
    email = data.get('email')                  # optional sanity only
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

    # Cooldown — per (email_hash, client_ip)
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    key = (email_hash, client_ip)
    now = datetime.now(tz=SGT)
    last_attempt = otp_cooldown.get(key)
    if last_attempt and (now - last_attempt) < timedelta(seconds=10):
        return jsonify({'error': 'Too many attempts. Please wait.'}), 429

    # Allow ±30s clock skew
    totp = pyotp.TOTP(voter.totp_secret)
    if not totp.verify(otp, valid_window=1):       # ← changed
        otp_cooldown[key] = now                    # ← changed
        return jsonify({'error': 'Invalid OTP'}), 401

    # Mark DB as logged in
    voter.logged_in = True
    voter.logged_in_2fa = True
    voter.last_2fa_at = now
    db.session.commit()

    # Clear cooldown for this user+ip
    otp_cooldown.pop(key, None)                    # ← changed

    # Rotate session to avoid fixation (keep the SAME keys your app expects)
    session.clear()                                 # ← new
    session['email'] = email_hash                   # keep existing name to avoid breaking other code
    session['role'] = voter.vote_role
    session['twofa'] = True
    session['login_at'] = now.isoformat()
    
    now_ts = int(time())
    session['sess_created_at'] = now_ts
    session['sess_last_seen']  = now_ts
    # (optional) make session last a workday in prod
    # session.permanent = True
    # current_app.permanent_session_lifetime = timedelta(hours=8)

    return jsonify({'message': '2FA successful. Access granted.', 'role': voter.vote_role}), 200
