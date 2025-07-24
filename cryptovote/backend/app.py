from flask import Flask, request, jsonify
from models.db import db  # use from models.db
from routes.register import register_bp
from routes.auth import auth_bp  # login
from routes.twofa import otp_bp
from routes.logout import logout_bp
from routes.cast_vote import cast_vote_bp
from routes.blind_sign import blind_sign_bp
from routes.admin_routes import admin_bp
from dotenv import load_dotenv
from utilities.network_utils import is_ntu_ip
import os

# Load environment variables
load_dotenv()

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.config.from_pyfile("config.py")
app.secret_key = os.getenv("SECRET_KEY")

# Init DB
db.init_app(app)

# Register Blueprints
app.register_blueprint(register_bp, url_prefix='/register')
app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(otp_bp)
app.register_blueprint(logout_bp, url_prefix="/logout")
app.register_blueprint(cast_vote_bp)
app.register_blueprint(blind_sign_bp)
app.register_blueprint(admin_bp, url_prefix="/admin")

# IP Restriction Middleware
@app.before_request
def restrict_to_ntu_wifi():
    # 🧪 Bypass in development mode
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
