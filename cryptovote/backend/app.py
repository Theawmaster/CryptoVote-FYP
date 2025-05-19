from flask import Flask
from models.db import db  # ✅ use from models.db
from routes.register import register_bp
from routes.auth import auth_bp #login
from routes.twofa import otp_bp 
from routes.logout import logout_bp
from routes.cast_vote import cast_vote_bp
from routes.blind_sign import blind_sign_bp
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

app = Flask(__name__)
app.config.from_pyfile("config.py")

db.init_app(app)
app.register_blueprint(register_bp, url_prefix='/register')
app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(otp_bp)
app.register_blueprint(logout_bp, url_prefix="/logout")
app.register_blueprint(cast_vote_bp)
app.register_blueprint(blind_sign_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5010)
