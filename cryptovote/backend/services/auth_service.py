from datetime import datetime, timedelta
from models.voter import Voter
from services.registration_service import generate_nonce, verify_voter_signature
from _zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

# In-memory nonce store
nonce_store = {}
NONCE_TTL_SECONDS = 300

def get_email_hash(email):
    import hashlib
    return hashlib.sha256(email.encode()).hexdigest()

def request_nonce(email_hash):
    from datetime import datetime
    nonce = generate_nonce()
    nonce_store[email_hash] = {
        'nonce': nonce,
        'issued_at': datetime.now(SGT)
    }
    return nonce

def validate_nonce(email_hash):
    record = nonce_store.get(email_hash)
    if not record:
        return None, 'Nonce not found or expired'
    
    if datetime.now(SGT) - record['issued_at'] > timedelta(seconds=NONCE_TTL_SECONDS):
        del nonce_store[email_hash]
        return None, 'Nonce expired. Please retry authentication.'

    return record['nonce'], None

def clear_nonce(email_hash):
    nonce_store.pop(email_hash, None)
