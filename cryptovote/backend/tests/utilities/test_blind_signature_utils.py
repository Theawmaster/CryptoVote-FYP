import pytest
from Crypto.PublicKey import RSA
from utilities import blind_signature_utils as utils
from pathlib import Path

@pytest.fixture()
def isolated_keys(tmp_path, monkeypatch):
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    monkeypatch.setattr(utils, "KEY_DIR", str(key_dir))
    monkeypatch.setattr(utils, "PRIVATE_KEY_PATH", str(key_dir / "rsa_private.pem"))
    monkeypatch.setattr(utils, "PUBLIC_KEY_PATH", str(key_dir / "rsa_public.pem"))
    return key_dir

def test_generate_and_load_keypair(isolated_keys):
    utils.generate_rsa_keypair()

    priv = utils.load_private_key()
    pub = utils.load_public_key()

    assert isinstance(priv, RSA.RsaKey)
    assert isinstance(pub, RSA.RsaKey)
    assert priv.has_private()
    assert not pub.has_private()

def test_blind_and_unblind_signature(isolated_keys):
    utils.generate_rsa_keypair()
    pubkey = utils.load_public_key()
    token = b"vote123"

    blinded, r = utils.blind_token(pubkey, token)
    signed = utils.sign_blinded_token(blinded)
    unblinded = utils.unblind_signature(signed, r)
    assert utils.verify_signed_token(pubkey, token, unblinded)

def test_verify_signed_token_invalid(isolated_keys):
    utils.generate_rsa_keypair()
    pubkey = utils.load_public_key()
    token = b"vote456"
    fake_signature = 123456789
    assert utils.verify_signed_token(pubkey, token, fake_signature) is False

def test_sign_blinded_token_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "PRIVATE_KEY_PATH", str(tmp_path / "missing_priv.pem"))
    with pytest.raises(FileNotFoundError):
        utils.sign_blinded_token(123456)

def test_load_public_key_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "PUBLIC_KEY_PATH", str(tmp_path / "missing_pub.pem"))
    with pytest.raises(FileNotFoundError):
        utils.load_public_key()

def test_gcd_cases():
    assert utils.gcd(54, 24) == 6
    assert utils.gcd(101, 10) == 1
    assert utils.gcd(0, 1) == 1
    assert utils.gcd(0, 0) == 0
    assert utils.gcd(1, 0) == 1
    assert utils.gcd(1, 1) == 1

def test_blind_token_retries_until_coprime(isolated_keys):
    utils.generate_rsa_keypair()
    pubkey = utils.load_public_key()
    token = b"force_retry"

    # Monkeypatch gcd to force a retry the first time
    original_gcd = utils.gcd
    call_count = {"count": 0}
    
    def fake_gcd(a, b):
        call_count["count"] += 1
        return 2 if call_count["count"] == 1 else original_gcd(a, b)

    utils.gcd = fake_gcd
    try:
        blinded, r = utils.blind_token(pubkey, token)
        assert isinstance(blinded, int)
        assert isinstance(r, int)
    finally:
        utils.gcd = original_gcd
