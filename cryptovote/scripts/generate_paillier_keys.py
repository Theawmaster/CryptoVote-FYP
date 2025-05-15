# scripts/generate_keys.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.services.paillier_utils import generate_paillier_keypair

generate_paillier_keypair()
