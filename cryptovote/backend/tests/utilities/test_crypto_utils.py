import os
import tempfile
import re
from utilities import crypto_utils as utils


def test_generate_rsa_key_pair_returns_pem():
    private_pem, public_pem = utils.generate_rsa_key_pair()
    assert private_pem.startswith("-----BEGIN RSA PRIVATE KEY-----")
    assert public_pem.startswith("-----BEGIN PUBLIC KEY-----")

def test_generate_rsa_key_pair_saves_to_disk():
    with tempfile.TemporaryDirectory() as tmp_dir:
        scripts_path = os.path.join(tmp_dir, "../../keys")
        os.makedirs(scripts_path, exist_ok=True)

        # Patch os.path.dirname to return the temp dir
        original_dirname = os.path.dirname
        os.path.dirname = lambda _: tmp_dir

        try:
            private_pem, public_pem = utils.generate_rsa_key_pair(save_to_disk=True)
            assert os.path.exists(os.path.join(scripts_path, "mykey.pem"))
        finally:
            os.path.dirname = original_dirname
