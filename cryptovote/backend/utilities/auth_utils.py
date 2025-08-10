# utilities/auth_utils.py
from functools import wraps
from flask import session, jsonify

def role_required(role):
    def deco(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if session.get('role') != role:
                return jsonify({'error': 'forbidden'}), 403
            if session.get('twofa') is not True:
                return jsonify({'error': '2fa_required'}), 403
            return fn(*args, **kwargs)
        return wrapped
    return deco

