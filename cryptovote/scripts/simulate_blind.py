import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.blind_signature_utils import load_public_key, blind_token
import secrets

# Step 1: Generate original token
token = "voteforA123"  # You can also use: secrets.token_hex(16)
print("🔑 Original token:", token)

# Step 2: Load public key and blind the token
pubkey = load_public_key()
blinded_int, r = blind_token(pubkey, token.encode())
blinded_hex = hex(blinded_int)[2:]  # Remove '0x'

print("# Blinded token (hex):", blinded_hex)
print("# Save r for unblinding:", r)
