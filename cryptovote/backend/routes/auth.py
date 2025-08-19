from flask import Blueprint, request, jsonify, session
from services.auth_service import get_email_hash, request_nonce, validate_nonce, clear_nonce
from services.registration_service import verify_voter_signature
from utilities.anomaly_utils import flag_suspicious_activity, failed_logins_last_10min
from models.voter import Voter
from models.db import db
from datetime import datetime
from _zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

auth_bp = Blueprint('auth', __name__)

def _finish_signature_phase(email: str, signed_nonce: str | None):
    """
    Shared logic for login/admin-login:
    - If no signed_nonce: return a fresh nonce
    - If signed_nonce present: verify and prepare session (twofa=False)
    Returns (response_json, status_code) or (None, None) if caller should continue.
    """
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    email_hash = get_email_hash(email)
    voter = Voter.query.filter_by(email_hash=email_hash).first()

    if not voter or not voter.is_verified:
        return jsonify({'error': 'Unverified or unknown user.'}), 403

    # If the client is only requesting a nonce
    if not signed_nonce:
        if voter.logged_in and getattr(voter, "logged_in_2fa", False):
            # Already fully signed in
            return jsonify({'message': 'You are already signed in.'}), 200

        nonce = request_nonce(email_hash)
        return jsonify({'nonce': nonce}), 200

    # Otherwise, validate the previously issued nonce and the signature
    nonce, error = validate_nonce(email_hash)
    if error:
        return jsonify({'error': error}), 403

    ok, msg = verify_voter_signature(email, signed_nonce, nonce)
    if not ok:
        flag_suspicious_activity(email, request.remote_addr, "Failed signature check", request.path)
        if failed_logins_last_10min(request.remote_addr) > 3:
            flag_suspicious_activity(email, request.remote_addr, "Multiple failed logins from same IP", request.path)
        return jsonify({'error': msg}), 401

    # Clear nonce and return control to the caller to set role policy
    clear_nonce(email_hash)
    return None, None  # caller continues


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    signed_nonce = data.get('signed_nonce')

    # Step 1: signature phase (issue nonce or verify)
    res, code = _finish_signature_phase(email, signed_nonce)
    if res is not None:
        return res, code  # either returned nonce or an error

    # Step 2: signature verified -> update DB flags and set a session with twofa=False
    email_hash = get_email_hash(email)
    voter = Voter.query.filter_by(email_hash=email_hash).first()

    try:
        voter.logged_in = False
        voter.logged_in_2fa = False  # will be set True on /2fa-verify
        voter.last_login_ip = request.remote_addr
        voter.last_login_at = datetime.now(SGT)
        db.session.commit()

        session['email'] = email_hash
        session['role'] = voter.vote_role or 'voter'
        session['twofa'] = False
        session['twofa_started_at'] = datetime.now(SGT).isoformat()
        session.modified = True

        return jsonify({
            'message': 'Signature verified. Please complete 2FA.',
            'email': email_hash,
            'pending_2fa': True,
            'role': session['role'],
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Verified but failed to update signature state.'}), 500


@auth_bp.route('/admin-login', methods=['POST'])
def admin_login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    signed_nonce = data.get('signed_nonce')

    # Step 1: signature phase (issue nonce or verify)
    res, code = _finish_signature_phase(email, signed_nonce)
    if res is not None:
        return res, code  # either returned nonce or an error

    # Step 2: enforce admin role and set twofa=False
    email_hash = get_email_hash(email)
    voter = Voter.query.filter_by(email_hash=email_hash).first()

    if voter.vote_role != 'admin':
        return jsonify({'error': 'Access denied. Not an admin.'}), 403

    try:
        voter.logged_in = False
        voter.logged_in_2fa = False
        voter.last_login_ip = request.remote_addr
        voter.last_login_at = datetime.now(SGT)
        db.session.commit()

        session['email'] = email_hash
        session['role'] = 'admin'
        session['twofa'] = False
        session['twofa_started_at'] = datetime.now(SGT).isoformat()
        session.modified = True

        return jsonify({
            'message': 'Admin signature verified. Please complete 2FA.',
            'email': email_hash,
            'last_login_ip': voter.last_login_ip,
            'last_login_at': voter.last_login_at,
            'pending_2fa': True,
            'role': 'admin'
        }), 200

    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Login verified but DB update failed.'}), 500



# @auth_bp.route('/admin/dev-login-admin', methods=['GET'])
# def dev_login_admin():
#     try:
#         email_hash = request.args.get("email_hash")
#         if not email_hash:
#             return jsonify({"error": "Missing email_hash parameter"}), 400

#         voter = Voter.query.filter_by(email_hash=email_hash).first()
#         if not voter:
#             return jsonify({"error": "No voter found with this hash"}), 404

#         if voter.vote_role != "admin":
#             return jsonify({"error": "Access denied: not an admin"}), 403

#         session["email"] = email_hash
#         session["role"] = "admin"

#         return jsonify({"message": f"Dev login successful as admin: {email_hash}"}), 200

#     except Exception as e:
#         print(f" Error in /dev-login-admin: {e}")
#         return jsonify({"error": "Internal server error"}), 500
