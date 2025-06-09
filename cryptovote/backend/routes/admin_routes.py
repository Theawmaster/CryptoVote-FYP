from flask import Blueprint
from routes.admin.election_routes import election_bp
from routes.admin.audit_routes import audit_bp
from routes.admin.download_routes import download_bp

admin_bp = Blueprint("admin", __name__)

# Mount modular route blueprints under /admin
admin_bp.register_blueprint(election_bp)
admin_bp.register_blueprint(audit_bp)
admin_bp.register_blueprint(download_bp)
