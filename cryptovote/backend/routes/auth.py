from flask import Blueprint, request, jsonify, session
from utilities.anomaly_utils import flag_suspicious_activity
from services.auth_service import (
    get_email_hash, request_nonce, validate_nonce, clear_nonce
)
from services.registration_service import verify_voter_signature
from models.voter import Voter
from models.db import db
from datetime import datetime
from utilities.anomaly_utils import flag_suspicious_activity, failed_logins_last_10min
from _zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

auth_bp = Blueprint('login', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    signed_nonce = data.get('signed_nonce')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    email_hash = get_email_hash(email)
    voter = Voter.query.filter_by(email_hash=email_hash).first()

    if not voter or not voter.is_verified:
        return jsonify({'error': 'Unverified or unknown voter.'}), 403

    if not signed_nonce:
        if voter.logged_in:
            return jsonify({'message': 'You are already signed in.'}), 200

        nonce = request_nonce(email_hash)
        return jsonify({'nonce': nonce})


    # Step 2: Validate and verify
    nonce, error = validate_nonce(email_hash)
    if error:
        return jsonify({'error': error}), 403

    success, msg = verify_voter_signature(email, signed_nonce, nonce)
    print("Backend received signed_nonce:", signed_nonce)
    print("Backend received nonce:", repr(nonce))
    if not success:
        flag_suspicious_activity(email, request.remote_addr, "Failed login attempt", "/login")
        
        if failed_logins_last_10min(request.remote_addr) > 3:
            flag_suspicious_activity(email, request.remote_addr, "Multiple failed logins from same IP", "/login")
        
        return jsonify({'error': msg}), 401

    clear_nonce(email_hash)

    try:
        voter.logged_in = True
        voter.last_login_ip = request.remote_addr
        voter.last_login_at = datetime.now(SGT)
        db.session.commit()
        print(f"✅ [{datetime.now(SGT)}] Login successful for {email_hash}")
        return jsonify({'message': 'Signature verified. Login successful.'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ DB update failed: {e}")
        return jsonify({'error': 'Verified but failed to update signature state.'}), 500

@auth_bp.route('/admin/dev-login-admin', methods=['GET'])
def dev_login_admin():
    try:
        email_hash = request.args.get("email_hash")
        if not email_hash:
            return jsonify({"error": "Missing email_hash parameter"}), 400

        voter = Voter.query.filter_by(email_hash=email_hash).first()
        if not voter:
            return jsonify({"error": "No voter found with this hash"}), 404

        if voter.vote_role != "admin":
            return jsonify({"error": "Access denied: not an admin"}), 403

        session["email"] = email_hash
        session["role"] = "admin"

        return jsonify({"message": f"Dev login successful as admin: {email_hash}"}), 200

    except Exception as e:
        print(f" Error in /dev-login-admin: {e}")
        return jsonify({"error": "Internal server error"}), 500
