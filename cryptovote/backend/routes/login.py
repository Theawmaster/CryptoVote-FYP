# routes/login.py
from flask import Blueprint

login_bp = Blueprint('login', __name__)

@login_bp.route('/login')
def login():
    return {"message": "Login route works."}
