import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_rsa_key_pair(save_to_disk=False):
    # Generate private key
    private_key_obj = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Export private key in PEM format
    private_pem = private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,  # PKCS#1
        encryption_algorithm=serialization.NoEncryption()  # or BestAvailableEncryption(b"pass")
    )

    # Export public key in PEM format
    public_pem = private_key_obj.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Save to scripts/mykey.pem
    if save_to_disk:
        scripts_path = os.path.join(os.path.dirname(__file__), "../../scripts")
        os.makedirs(scripts_path, exist_ok=True)

        key_path = os.path.join(scripts_path, "mykey.pem")
        with open(key_path, "wb") as f:
            f.write(private_pem)

        print(f"✅ Saved private key to {key_path}")

    return private_pem.decode("utf-8"), public_pem.decode("utf-8")
