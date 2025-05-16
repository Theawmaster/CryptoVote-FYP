import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.paillier_utils import encrypt_vote

vote = 1  # Simulate vote for candidate 1
encrypted = encrypt_vote(vote)

print("🔐 Ciphertext:", encrypted['ciphertext'])
print("🧠 Exponent:", encrypted['exponent'])
