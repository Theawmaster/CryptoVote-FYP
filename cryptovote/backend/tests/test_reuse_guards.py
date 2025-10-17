# backend/tests/test_cast_vote_signature.py
import os
import pytest
from flask import Flask
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from utilities.verification.vote_verification_utils import parse_and_verify_signature

@pytest.fixture(scope="module", autouse=True)
def flask_app_ctx():
    app = Flask(__name__)
    app.config["TESTING"] = True
    with app.app_context():
        yield

@pytest.fixture(scope="module")
def rsa_keypair():
    key = RSA.generate(2048)
    return key, key.publickey()

def _raw_rsa_sign_hex(token: str, priv: RSA.RsaKey) -> str:
    m = int.from_bytes(SHA256.new(token.encode("utf-8")).digest(), "big")
    s = pow(m, priv.d, priv.n)
    return f"{s:x}"

def test_signature_valid_then_token_byte_change_fails(rsa_keypair):
    priv, pub = rsa_keypair
    token = "vote-token-" + os.urandom(8).hex()
    sig_hex = _raw_rsa_sign_hex(token, priv)
    ok, sig_back, err = parse_and_verify_signature(token, sig_hex, pub)
    assert ok and err is None and isinstance(sig_back, int)
    tampered = token[:-1] + ("0" if token[-1] != "0" else "1")
    ok2, _, code2 = parse_and_verify_signature(tampered, sig_hex, pub)
    assert not ok2 and code2 == 403

def test_signature_bitflip_fails(rsa_keypair):
    priv, pub = rsa_keypair
    token = "scoped-token-" + os.urandom(8).hex()
    sig_hex = _raw_rsa_sign_hex(token, priv)
    tampered_sig_hex = f"{(int(sig_hex, 16) ^ 1):x}"
    ok, _, code = parse_and_verify_signature(token, tampered_sig_hex, pub)
    assert not ok and code == 403

def test_malformed_signature_hex_is_rejected(rsa_keypair):
    _, pub = rsa_keypair
    token = "tkn-" + os.urandom(4).hex()
    ok, _, code = parse_and_verify_signature(token, "zz11", pub)
    assert not ok and code == 400
