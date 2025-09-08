from datetime import timedelta
from extensions import limiter
from flask import Flask, request, jsonify
from models.db import db  # use from models.db
from routes.register import register_bp
from routes.auth import auth_bp  # login
from routes.twofa import otp_bp
from routes.whoami import whoami_bp
from routes.logout import logout_bp
from routes.cast_vote import cast_vote_bp
from routes.blind_sign import blind_sign_bp
from routes.admin.admin_routes import admin_bp
from routes.voter_routes import voter_bp
from routes.candidate_list import candidate_list_bp
from routes.admin.audit_routes import audit_bp
from routes.admin.download_routes import download_bp
from routes.admin.election_routes import election_bp
from routes.admin.security_routes import bp as security_bp
from routes.admin.admin_me import bp_me
from routes.public_keys import keys_bp
from dotenv import load_dotenv
from utilities.network_utils import is_ntu_ip
from routes.receipt import receipt_bp
from routes.results import results_bp
from routes.wbb import wbb_bp
from utilities.session_utils import register_session_ttl
from flask_cors import CORS 
import os

# Load environment variables
load_dotenv()

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.config.from_pyfile("config.py")
app.secret_key = os.getenv("SECRET_KEY")

# init limiter
limiter.init_app(app)

is_dev = app.debug or os.getenv("FLASK_ENV") == "development"

app.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev-not-for-prod"),
    SESSION_COOKIE_NAME="cryptovote_sess",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,   # True only behind HTTPS
    SESSION_COOKIE_SAMESITE="Lax", # use a dev proxy so Lax works
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)


CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:3000"}},
    supports_credentials=True,  # set True later you use cookies
)

# Init DB
db.init_app(app)

# Register Blueprints
app.register_blueprint(register_bp, url_prefix='/register')
app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(otp_bp)
app.register_blueprint(logout_bp, url_prefix="/logout")
app.register_blueprint(cast_vote_bp)
app.register_blueprint(blind_sign_bp)
app.register_blueprint(whoami_bp)
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(voter_bp, url_prefix="/voter")
app.register_blueprint(audit_bp,    url_prefix="/admin")
app.register_blueprint(download_bp, url_prefix="/admin")
app.register_blueprint(election_bp, url_prefix="/admin")
app.register_blueprint(bp_me, url_prefix="/admin")
app.register_blueprint(security_bp, url_prefix="/admin")
app.register_blueprint(candidate_list_bp, url_prefix="/voter")
app.register_blueprint(receipt_bp)
app.register_blueprint(results_bp)
app.register_blueprint(keys_bp)
app.register_blueprint(wbb_bp)
register_session_ttl(app, idle_ttl=2*60, abs_ttl=8*60*60)

# IP Restriction Middleware
@app.before_request
def restrict_to_ntu_wifi():
    # Bypass in development mode
    if os.getenv("FLASK_ENV") == "development" or app.debug:
        return

    # Validate IP
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if not is_ntu_ip(client_ip):
        return jsonify({
            "error": "Access restricted to NTU WiFi only.",
            "your_ip": client_ip
        }), 403

# --- Health endpoint (good for demo) ---
@app.get("/healthz")
@limiter.exempt                        # never throttle health
def healthz():
    return {"ok": True, "service": "cryptovote"}

# --- Nice JSON for rate-limit blocks (demo will show 429s) ---
@app.errorhandler(429)
def handle_ratelimit(e):
    return jsonify(error="Too Many Requests", detail=str(e.description)), 429

# DB Table Creation
with app.app_context():
    db.create_all()

# Launch App
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5010) # Change debug to False in production to trigger IP restriction
