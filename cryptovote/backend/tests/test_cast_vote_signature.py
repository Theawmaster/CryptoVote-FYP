# backend/tests/test_cast_vote_signature.py
import os
import binascii
import hashlib
import pytest
from flask import Flask

from utilities.verification.vote_verification_utils import parse_and_verify_signature


# --- Flask app context so jsonify() works inside the util ---
@pytest.fixture(scope="module", autouse=True)
def flask_app_ctx():
    app = Flask(__name__)
    app.config["TESTING"] = True
    with app.app_context():
        yield


# --- A deterministic "sign" that mirrors our monkeypatched verifier ---
def _fake_sign(token: str) -> int:
    # Produce a big-int "signature" from the SHA-256 of the UTF-8 token.
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest, "big")


@pytest.fixture(autouse=True)
def patch_verify_signed_token(monkeypatch):
    """
    Monkeypatch utilities.blind_signature_utils.verify_signed_token
    so parse_and_verify_signature becomes testable without the real RSA impl.

    Contract we enforce:
      verify_signed_token(pubkey, token_bytes, signature_int) -> bool
      returns True iff signature_int == int(SHA256(token_bytes))
    """
    import types

    def fake_verify_signed_token(pubkey, token_bytes, signature_int) -> bool:
        digest = hashlib.sha256(token_bytes).digest()
        expected = int.from_bytes(digest, "big")
        return signature_int == expected

    # Patch the symbol that parse_and_verify_signature imports at runtime
    import utilities.blind_signature_utils as bs
    monkeypatch.setattr(bs, "verify_signed_token", fake_verify_signed_token, raising=True)

    # Provide a dummy "pubkey" object the util will pass through
    class DummyPub:  # shape doesn’t matter; it’s opaque to the fake verifier
        pass

    return types.SimpleNamespace(pub=DummyPub())


def test_signature_valid_then_token_byte_change_fails(patch_verify_signed_token):
    pub = patch_verify_signed_token.pub
    token = "vote-token-" + os.urandom(8).hex()

    # Produce a matching signature (hex) for this token
    sig_int = _fake_sign(token)
    sig_hex = f"{sig_int:x}"

    # ✅ Exact token + signature must pass
    ok, sig_back, err = parse_and_verify_signature(token, sig_hex, pub)
    assert ok and err is None and isinstance(sig_back, int)

    # ❌ Change one byte (really: one char) in the token -> must fail
    tampered_token = token[:-1] + ("0" if token[-1] != "0" else "1")
    ok2, _, _ = parse_and_verify_signature(tampered_token, sig_hex, pub)
    assert not ok2, "Signature must fail when the token changes by one byte"


def test_signature_bitflip_fails(patch_verify_signed_token):
    pub = patch_verify_signed_token.pub
    token = "scoped-token-" + os.urandom(8).hex()

    sig_int = _fake_sign(token)
    sig_hex = f"{sig_int:x}"

    # Flip 1 bit in the signature
    raw = bytearray(binascii.unhexlify(sig_hex if len(sig_hex) % 2 == 0 else "0" + sig_hex))
    raw[0] ^= 0x01
    tampered_sig_hex = raw.hex()

    ok, _, _ = parse_and_verify_signature(token, tampered_sig_hex, pub)
    assert not ok, "Signature must fail when a single bit is flipped"


def test_malformed_signature_hex_is_rejected(patch_verify_signed_token):
    pub = patch_verify_signed_token.pub
    token = "tkn-" + os.urandom(4).hex()

    bad_hex = "zz11"  # invalid hex
    ok, _, code = parse_and_verify_signature(token, bad_hex, pub)
    assert not ok and code == 400, "Non-hex signature input should be rejected with 400"
