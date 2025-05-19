import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.utilities.paillier_utils import generate_paillier_keypair

if __name__ == "__main__":
    generate_paillier_keypair()
    print("✅ Paillier keypair generated.")
