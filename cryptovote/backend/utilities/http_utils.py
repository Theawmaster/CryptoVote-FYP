# utilities/http_utils.py
from flask import jsonify, make_response

def too_many(msg="Too many requests", retry_secs=10):
    resp = make_response(jsonify({"error": msg, "retry_after": retry_secs}), 429)
    resp.headers["Retry-After"] = str(retry_secs)
    return resp
