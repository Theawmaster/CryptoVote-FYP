# utilities/pii_hash.py
import os, hmac, hashlib

# IMPORTANT: Set this in production (e.g., in .env / deployment secrets)
# export SECRET_EMAIL_HMAC_KEY="a-long-random-secret"
_HMAC_KEY = os.environ.get("SECRET_EMAIL_HMAC_KEY", "dev-unsafe-key").encode()

def email_hmac(email: str | None) -> str | None:
    """Privacy-safe, consistent identifier for an email (non-reversible)."""
    if not email:
        return None
    return hmac.new(_HMAC_KEY, email.encode("utf-8"), hashlib.sha256).hexdigest()
