# routes/public_keys.py
from flask import Blueprint, jsonify
import hashlib

from utilities.blind_signature_utils import load_public_key as load_rsa_public_key
from utilities.paillier_utils import load_public_key as load_paillier_public_key
from utilities.key_fingerprint import fingerprint_paillier_n

keys_bp = Blueprint("keys", __name__)

def _rsa_numbers(pub):
    """
    Support both cryptography and PyCryptodome-style RSA public keys.
    Returns (n, e) as ints or raises ValueError.
    """
    # cryptography.hazmat RSAPublicKey
    try:
        nums = pub.public_numbers()  # type: ignore[attr-defined]
        return int(nums.n), int(nums.e)
    except Exception:
        pass
    # PyCryptodome RSA.RsaKey
    n = getattr(pub, "n", None)
    e = getattr(pub, "e", None)
    if n is None or e is None:
        raise ValueError("Unsupported RSA public key type")
    return int(n), int(e)

def _fingerprint(label: str, *parts: int) -> str:
    h = hashlib.sha256(("|".join([label, *map(str, parts)])).encode("utf-8")).hexdigest()
    return h[:12]  # short key id

@keys_bp.get("/public-keys")
def get_public_keys():
    """
    One-stop public keys endpoint for the frontend.

    Returns:
    {
      "rsa":      { "key_id", "nHex", "eDec", "bits" },
      "paillier": { "key_id", "nHex", "bits" }
    }
    """
    out = {}

    # RSA (for blind-sign)
    try:
        rsa_pub = load_rsa_public_key()
        n, e = _rsa_numbers(rsa_pub)
        out["rsa"] = {
            "key_id": f"rsa-{_fingerprint('rsa', n, e)}",
            "nHex": hex(n)[2:],         # hex modulus without 0x
            "eDec": str(e),             # decimal exponent (e.g., 65537)
            "bits": n.bit_length(),
        }
    except Exception as exc:
        out["rsa_error"] = f"{type(exc).__name__}: {exc}"

    # Paillier (for ballot encryption client-side if ever needed)
    try:
        ppk = load_paillier_public_key()
        n = int(ppk.n)
        out["paillier"] = {
            "key_id": fingerprint_paillier_n(n),
            "nHex": hex(n)[2:],
            "bits": n.bit_length(),
        }
    except Exception as exc:
        out["paillier_error"] = f"{type(exc).__name__}: {exc}"

    resp = jsonify(out)
    resp.headers["Cache-Control"] = "public, max-age=300"
    return resp, 200

# (Optional) narrower endpoints if you prefer:
@keys_bp.get("/public-keys/rsa")
def get_rsa_key():
    rsa_pub = load_rsa_public_key()
    n, e = _rsa_numbers(rsa_pub)
    return jsonify({
        "key_id": f"rsa-{_fingerprint('rsa', n, e)}",
        "nHex": hex(n)[2:], "eDec": str(e), "bits": n.bit_length(),
    }), 200

@keys_bp.get("/public-keys/paillier")
def get_paillier_key():
    ppk = load_paillier_public_key()
    n = int(ppk.n)
    return jsonify({
        "key_id": f"paillier-{_fingerprint('paillier', n)}",
        "nHex": hex(n)[2:], "bits": n.bit_length(),
    }), 200
