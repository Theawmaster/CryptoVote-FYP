import json
from phe import paillier
import os

KEYS_DIR = os.path.join(os.path.dirname(__file__), '../../keys/')
os.makedirs(KEYS_DIR, exist_ok=True)

def generate_paillier_keypair():
    public_key, private_key = paillier.generate_paillier_keypair()

    # Save public key
    with open(os.path.join(KEYS_DIR, 'paillier_public_key.json'), 'w') as f:
        json.dump({
            'n': public_key.n
        }, f)

    # Save private key
    with open(os.path.join(KEYS_DIR, 'paillier_private_key.json'), 'w') as f:
        json.dump({
            'p': private_key.p,
            'q': private_key.q,
            'public_key_n': private_key.public_key.n
        }, f)

    print("✅ Paillier keys generated and saved.")

def load_public_key():
    with open(os.path.join(KEYS_DIR, 'paillier_public_key.json'), 'r') as f:
        data = json.load(f)
    return paillier.PaillierPublicKey(n=int(data['n']))

def load_private_key():
    pub = load_public_key()
    with open(os.path.join(KEYS_DIR, 'paillier_private_key.json'), 'r') as f:
        data = json.load(f)
    return paillier.PaillierPrivateKey(public_key=pub, p=int(data['p']), q=int(data['q']))

def encrypt_vote(candidate_id: int):
    pubkey = load_public_key()
    encrypted = pubkey.encrypt(candidate_id)
    return {
        'ciphertext': str(encrypted.ciphertext()),
        'exponent': encrypted.exponent
    }

def decrypt_vote(ciphertext: str, exponent: int):
    privkey = load_private_key()
    pubkey = load_public_key()
    encrypted_number = paillier.EncryptedNumber(pubkey, int(ciphertext), int(exponent))
    return privkey.decrypt(encrypted_number)
