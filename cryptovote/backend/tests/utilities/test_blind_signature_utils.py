import pytest
from Crypto.PublicKey import RSA
from utilities import blind_signature_utils as utils

def test_generate_and_load_keypair(tmp_path, monkeypatch):
    # Redirect the key path to a temp directory
    test_key_dir = tmp_path / "keys"
    monkeypatch.setattr(utils, "KEY_DIR", str(test_key_dir))
    monkeypatch.setattr(utils, "PRIVATE_KEY_PATH", str(test_key_dir / "rsa_private.pem"))
    monkeypatch.setattr(utils, "PUBLIC_KEY_PATH", str(test_key_dir / "rsa_public.pem"))

    utils.generate_rsa_keypair()

    priv = utils.load_private_key()
    pub = utils.load_public_key()

    assert isinstance(priv, RSA.RsaKey)
    assert isinstance(pub, RSA.RsaKey)
    assert priv.has_private()
    assert pub.has_private() is False

def test_blind_and_unblind_signature():
    utils.generate_rsa_keypair()
    pubkey = utils.load_public_key()
    privkey = utils.load_private_key()

    token = b"vote123"
    blinded, r = utils.blind_token(pubkey, token)
    signed_blinded = utils.sign_blinded_token(blinded)
    unblinded = utils.unblind_signature(signed_blinded, r)

    # Validate final signature
    is_valid = utils.verify_signed_token(pubkey, token, unblinded)
    assert is_valid

def test_gcd():
    assert utils.gcd(54, 24) == 6
    assert utils.gcd(101, 10) == 1
    assert utils.gcd(0, 1) == 1
    assert utils.gcd(0, 0) == 0
    assert utils.gcd(1, 0) == 1
    assert utils.gcd(1, 1) == 1
