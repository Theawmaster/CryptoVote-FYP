from Crypto.PublicKey import RSA
from Crypto.Random import random
from Crypto.Util.number import inverse
from Crypto.Hash import SHA256
import os


# RSA key file paths
KEY_DIR = os.path.join(os.path.dirname(__file__), '../../keys/')
PRIVATE_KEY_PATH = os.path.join(KEY_DIR, 'rsa_private.pem')
PUBLIC_KEY_PATH = os.path.join(KEY_DIR, 'rsa_public.pem')

# === 1. Generate RSA Keypair ===
def generate_rsa_keypair():
    os.makedirs(KEY_DIR, exist_ok=True)
    private_key = RSA.generate(2048)
    with open(PRIVATE_KEY_PATH, 'wb') as f:
        f.write(private_key.export_key('PEM'))
    with open(PUBLIC_KEY_PATH, 'wb') as f:
        f.write(private_key.publickey().export_key('PEM'))

# === 2. Load Keys ===
def load_private_key():
    with open(PRIVATE_KEY_PATH, 'rb') as f:
        return RSA.import_key(f.read())

def load_public_key():
    with open(PUBLIC_KEY_PATH, 'rb') as f:
        return RSA.import_key(f.read())

# === 3. Blind the token ===
def blind_token(pubkey, message: bytes):
    digest = SHA256.new(message).digest()
    m = int.from_bytes(digest, 'big')
    n, e = pubkey.n, pubkey.e
    while True:
        r = random.StrongRandom().randint(1, n - 1)
        if gcd(r, n) == 1:
            break
    blinded = (pow(r, e, n) * m) % n
    return blinded, r

# === 4. Sign the blinded token ===
def sign_blinded_token(blinded_int: int):
    privkey = load_private_key()
    return pow(blinded_int, privkey.d, privkey.n)

# === 5. Unblind the signature ===
def unblind_signature(signed_blinded_int, r):
    pubkey = load_public_key()  # Directly load the RSA key
    n = pubkey.n
    r_inv = pow(r, -1, n)
    return (signed_blinded_int * r_inv) % n


# === 6. Verify signature ===
def verify_signed_token(pubkey, message: bytes, signature_int: int):
    digest = SHA256.new(message).digest()
    m = int.from_bytes(digest, 'big')
    return pow(signature_int, pubkey.e, pubkey.n) == m


# === Helper GCD ===
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

# === Demo ===
# if __name__ == "__main__":
#     if not os.path.exists(PRIVATE_KEY_PATH) or not os.path.exists(PUBLIC_KEY_PATH):
#         generate_rsa_keypair()
#         print("RSA key pair generated.")
#     else:
#         print("RSA key pair already exists.")

#     pub = load_public_key()
#     priv = load_private_key()

#     token = b"voteforA123"

#     # Step 1: Blind
#     blinded, r = blind_token(pub, token)
#     print("Blinded int:", blinded)

#     # Step 2: Sign
#     signed_blinded = sign_blinded_token(blinded)
#     print("Signed blinded:", signed_blinded)

#     # Step 3: Unblind
#     unblinded_sig = unblind_token(pub, signed_blinded, r)
#     print("Unblinded signature:", unblinded_sig)

#     # Step 4: Verify
#     is_valid = verify_signed_token(pub, token, unblinded_sig)
#     print("✅ Signature valid:", is_valid)
