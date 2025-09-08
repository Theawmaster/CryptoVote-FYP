# utilities/rate_limit_utils.py
import time, redis, os
from flask import jsonify, make_response

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

def allow(ip: str, key: str = "", max_attempts=5, window_secs=30):
    """
    Returns True if allowed, False if rate limited.
    Tracks attempts in Redis with expiry.
    """
    now = int(time.time())
    bucket = f"rl:{key}:{ip}:{now // window_secs}"  # discrete window
    count = r.incr(bucket)
    if count == 1:
        r.expire(bucket, window_secs)
    return count <= max_attempts

def too_many(msg: str = "Too many requests", retry_secs: int = 10):
    resp = make_response(jsonify({"error": msg, "retry_after": retry_secs}), 429)
    resp.headers["Retry-After"] = str(retry_secs)
    return resp