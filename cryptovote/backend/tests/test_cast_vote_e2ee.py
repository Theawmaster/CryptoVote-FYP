# backend/tests/test_cast_vote_e2ee.py
import json
import hashlib
import secrets

from models.encrypted_candidate_vote import EncryptedCandidateVote

def _login(client):
    """Mark test client as authenticated voter."""
    with client.session_transaction() as s:
        s["email"] = "testhash@example"

def _fingerprint_key(pub):
    """Return the expected Paillier key fingerprint, same as in server code."""
    n = int(pub.n)
    h = hashlib.sha256(f"paillier|{n}".encode("utf-8")).hexdigest()
    return f"paillier-{h[:12]}"

def _build_ballot(pub, cids, chosen):
    """Build a valid Paillier one-hot ballot for the given candidate IDs."""
    entries = []
    for cid in cids:
        bit = 1 if cid == chosen else 0
        c = str(pub.encrypt(bit).ciphertext())
        entries.append({"candidate_id": cid, "c": c})
    return {
        "scheme": "paillier-1hot",
        "key_id": _fingerprint_key(pub),
        "exponent": 0,
        "entries": entries,
    }

def _post_cast_vote(client, payload):
    """Helper: POST /cast-vote with JSON and return response."""
    return client.post(
        "/cast-vote",
        data=json.dumps(payload),
        content_type="application/json"
    )

def _with_tracker(payload):
    """Ensure payload includes a valid tracker (so ballot validation runs)."""
    payload["tracker"] = secrets.token_hex(8)  # 16 hex chars
    return payload

# ---- Tests ----

def test_e2ee_accepts_and_stores_ciphertexts(app, client):
    _login(client)
    cids = ["c1", "c2", "c3"]
    ballot = _build_ballot(app._pub, cids, chosen="c2")
    payload = _with_tracker({
        "election_id": "election_demo",
        "token": "tkn",
        "signature": "sig",
        "ballot": ballot,
    })
    r = _post_cast_vote(client, payload)
    assert r.status_code == 200, r.data

    # ONLY count vote rows (ignore WBB entries etc.)
    stored_votes = [x for x in app._added if isinstance(x, EncryptedCandidateVote)]
    assert len(stored_votes) == len(cids)

    for row in stored_votes:
        assert row.election_id == "election_demo"
        assert row.vote_exponent == 0
        v = int(row.vote_ciphertext)
        assert v < int(app._pub.n) ** 2

def test_reject_wrong_scheme(app, client):
    _login(client)
    ballot = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    ballot["scheme"] = "not-supported"
    payload = _with_tracker({"election_id": "E", "token": "t", "signature": "s", "ballot": ballot})
    r = _post_cast_vote(client, payload)
    assert r.status_code == 400
    assert b"unsupported_ballot_scheme" in r.data

def test_reject_length_mismatch(app, client):
    _login(client)
    b = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    b["entries"] = b["entries"][:-1]
    payload = _with_tracker({"election_id":"E","token":"t","signature":"s","ballot":b})
    r = _post_cast_vote(client, payload)
    assert r.status_code == 400
    assert b"ballot_length_mismatch" in r.data

def test_reject_duplicate_candidate_ids(app, client):
    _login(client)
    b = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    b["entries"][1]["candidate_id"] = "c1"
    payload = _with_tracker({"election_id":"E","token":"t","signature":"s","ballot":b})
    r = _post_cast_vote(client, payload)
    assert r.status_code == 400
    assert b"invalid_candidate_in_ballot" in r.data

def test_reject_non_integer_ciphertext(app, client):
    _login(client)
    b = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    b["entries"][0]["c"] = "not-an-int"
    payload = _with_tracker({"election_id":"E","token":"t","signature":"s","ballot":b})
    r = _post_cast_vote(client, payload)
    assert r.status_code == 400
    assert b"ciphertext_not_integer" in r.data

def test_reject_ciphertext_out_of_range(app, client):
    _login(client)
    b = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    b["entries"][0]["c"] = str(int(app._pub.n) ** 2)  # >= n^2
    payload = _with_tracker({"election_id":"E","token":"t","signature":"s","ballot":b})
    r = _post_cast_vote(client, payload)
    assert r.status_code == 400
    assert b"ciphertext_out_of_range" in r.data

def test_reject_key_id_mismatch(app, client):
    _login(client)
    b = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    b["key_id"] = "paillier-deadbeef"
    payload = _with_tracker({"election_id":"E","token":"t","signature":"s","ballot":b})
    r = _post_cast_vote(client, payload)
    assert r.status_code == 400
    assert b"paillier_key_mismatch" in r.data
