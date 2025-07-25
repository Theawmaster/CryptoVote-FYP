import re
import hashlib
import uuid

from cryptovote.backend.utilities.token_utils import generate_token, hash_token

def test_generate_token_format():
    token = generate_token()
    # Match UUIDv4 format
    assert re.fullmatch(
        r"[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}",
        token
    )

def test_generate_token_uniqueness():
    tokens = {generate_token() for _ in range(100)}
    assert len(tokens) == 100  # All unique

def test_hash_token_value():
    token = "test123"
    expected = hashlib.sha256(token.encode()).hexdigest()
    assert hash_token(token) == expected

def test_hash_token_consistency():
    token = "repeat_token"
    hash1 = hash_token(token)
    hash2 = hash_token(token)
    assert hash1 == hash2  # Same input gives same output
