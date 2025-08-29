# utilities/key_fingerprint.py
import hashlib

def fingerprint_paillier_n(n: int) -> str:
    h = hashlib.sha256(("|".join(["paillier", str(n)])).encode("utf-8")).hexdigest()
    return f"paillier-{h[:12]}"
