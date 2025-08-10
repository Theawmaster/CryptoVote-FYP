from datetime import timedelta
from flask import Flask, request, jsonify
from models.db import db  # use from models.db
from routes.register import register_bp
from routes.auth import auth_bp  # login
from routes.twofa import otp_bp
from routes.whoami import whoami_bp
from routes.logout import logout_bp
from routes.cast_vote import cast_vote_bp
from routes.blind_sign import blind_sign_bp
from routes.admin_routes import admin_bp
from routes.admin.audit_routes import audit_bp
from routes.admin.download_routes import download_bp
from routes.admin.election_routes import election_bp
from dotenv import load_dotenv
from utilities.network_utils import is_ntu_ip
from flask_cors import CORS 
import os

# Load environment variables
load_dotenv()

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.config.from_pyfile("config.py")
app.secret_key = os.getenv("SECRET_KEY")

is_dev = app.debug or os.getenv("FLASK_ENV") == "development"

app.config.update(
    SESSION_COOKIE_SAMESITE = 'Lax' if is_dev else 'None',
    SESSION_COOKIE_SECURE = not is_dev,             # False in dev (HTTP), True in prod (HTTPS)
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
app.register_blueprint(audit_bp,    url_prefix="/admin")
app.register_blueprint(download_bp, url_prefix="/admin")
app.register_blueprint(election_bp, url_prefix="/admin")

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

# DB Table Creation
with app.app_context():
    db.create_all()

# Launch App
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5010) # Change debug to False in production to trigger IP restriction
