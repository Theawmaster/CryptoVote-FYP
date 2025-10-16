# extensions.py
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

def demo_key_func():
    # For demo: let a header override the key so we can "separate" attacker traffic
    return request.headers.get("X-Real-IP") or get_remote_address()


storage = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
limiter = Limiter(get_remote_address, storage_uri=storage)

# Shared buckets for quick, consistent coverage
# - mutate: POST/PUT/DELETE (session-impacting)
# - auth:   login/2fa paths
# - read:   public GETs (keep high so UI feels snappy)
auth_limit   = limiter.shared_limit("5/second; 60/minute", scope="auth")
mutate_limit = limiter.shared_limit("3/second; 30/minute", scope="mutate")
read_limit   = limiter.shared_limit("30/second; 600/minute", scope="read")