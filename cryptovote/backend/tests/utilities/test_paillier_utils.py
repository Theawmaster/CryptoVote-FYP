import pytest
import os
import builtins
import json
from utilities import paillier_utils as utils
from phe import paillier

@pytest.fixture
def patch_key_loading(monkeypatch, tmp_path):
    # Point KEYS_DIR to temp
    keys_dir = tmp_path / "keys"
    keys_dir.mkdir()
    monkeypatch.setattr(utils, "KEYS_DIR", str(keys_dir))

    # Wrap original open to alias correct filenames
    original_open = builtins.open

    def patched_open(file, mode='r', *args, **kwargs):
        if file.endswith("public_key.json"):
            file = os.path.join(str(keys_dir), "paillier_public_key.json")
        elif file.endswith("private_key.json"):
            file = os.path.join(str(keys_dir), "paillier_private_key.json")
        return original_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", patched_open)

    return keys_dir

def test_generate_and_load_paillier_keys(patch_key_loading):
    utils.generate_paillier_keypair()

    assert os.path.exists(patch_key_loading / "paillier_public_key.json")
    assert os.path.exists(patch_key_loading / "paillier_private_key.json")

    pub = utils.load_public_key()
    priv = utils.load_private_key()

    assert isinstance(pub, paillier.PaillierPublicKey)
    assert isinstance(priv, paillier.PaillierPrivateKey)
    assert pub.n == priv.public_key.n

def test_encrypt_and_decrypt_vote(patch_key_loading):
    utils.generate_paillier_keypair()

    candidate_id = 3
    encrypted = utils.encrypt_vote(candidate_id)
    decrypted = utils.decrypt_vote(
        ciphertext=encrypted["ciphertext"],
        exponent=encrypted["exponent"]
    )

    assert decrypted == candidate_id
