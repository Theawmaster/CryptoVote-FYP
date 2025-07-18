import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.utilities.blind_signature_utils import (
    load_public_key,
    blind_token,
    generate_rsa_keypair,
    PRIVATE_KEY_PATH,
    PUBLIC_KEY_PATH
)
import secrets

# === Ensure RSA keys exist ===
if not os.path.exists(PRIVATE_KEY_PATH) or not os.path.exists(PUBLIC_KEY_PATH):
    generate_rsa_keypair()
    print("✅ RSA keypair generated.")

# Step 1: Generate original token
token = "voteforA123"
print("🔑 Original token:", token)

# Step 2: Load public key and blind the token
pubkey = load_public_key()
blinded_int, r = blind_token(pubkey, token.encode())
blinded_hex = hex(blinded_int)[2:]  # Remove '0x'

print("🕶️  Blinded token (hex):", blinded_hex)
print("🧮 Save r for unblinding:", r)
