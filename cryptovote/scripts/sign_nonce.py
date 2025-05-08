import argparse
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

def sign_nonce(private_key_path: str, nonce: str):
    # Load the RSA private key from the .pem file
    with open(private_key_path, 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    # Sign the nonce using SHA-256 and PKCS1v15
    signature = private_key.sign(
        nonce.encode(),
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    # Encode the signature as Base64
    signed_nonce_b64 = base64.b64encode(signature).decode()
    return signed_nonce_b64

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sign a nonce using RSA private key")
    parser.add_argument("--key", required=True, help="Path to the RSA private key (.pem)")
    parser.add_argument("--nonce", required=True, help="Nonce string to sign")

    args = parser.parse_args()

    try:
        signed = sign_nonce(args.key, args.nonce)
        print("\n✅ Signed Nonce (Base64):\n")
        print(signed)
    except Exception as e:
        print(f"\n❌ Error signing nonce: {e}")


# To run the script, use the following command:
# python scripts/sign_nonce.py --key scripts/mykey.pem --nonce "your_nonce_here"