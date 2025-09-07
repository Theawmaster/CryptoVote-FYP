# utilities/merkle.py
import hashlib

def h(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def hex_to_bytes(x: str) -> bytes:
    return bytes.fromhex(x)

def bytes_to_hex(b: bytes) -> str:
    return b.hex()

def merkle_root(leaves_hex: list[str]) -> str:
    if not leaves_hex:
        return "0" * 64
    level = [hex_to_bytes(x) for x in leaves_hex]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i+1] if i+1 < len(level) else level[i]
            nxt.append(h(a + b))
        level = nxt
    return bytes_to_hex(level[0])

def merkle_proof(leaves_hex: list[str], index: int) -> list[str]:
    """Return list of hex sibling hashes from bottom to top."""
    if not leaves_hex or index < 0 or index >= len(leaves_hex):
        return []
    level = [hex_to_bytes(x) for x in leaves_hex]
    idx = index
    proof = []
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i+1] if i+1 < len(level) else level[i]
            if i == idx ^ 1 or (i+1 == idx and i == idx - 1):
                # no-op; easier to compute sibling based on idx math below
                pass
            nxt.append(h(a + b))
        # sibling:
        sibling_idx = idx ^ 1
        if sibling_idx >= len(level):
            sibling_idx = idx  # last duplicated
        proof.append(bytes_to_hex(level[sibling_idx]))
        idx //= 2
        level = nxt
    return proof
