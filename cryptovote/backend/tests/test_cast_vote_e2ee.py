# backend/tests/test_cast_vote_e2ee.py
import json
import pytest

def _login(client):
    # Put a value in session['email'] so the route sees an authenticated voter
    with client.session_transaction() as s:
        s["email"] = "testhash@example"

def __key_id(pub):
    # Must match routes/public_keys.py fingerprinting (paillier|n -> sha256 -> first 12)
    import hashlib
    n = int(pub.n)
    h = hashlib.sha256(f"paillier|{n}".encode("utf-8")).hexdigest()
    return h[:12]

def _build_ballot(pub, cids, chosen):
    """
    Build a 'paillier-1hot' ballot: encrypt 1 for 'chosen', 0 for others.
    We only need ciphertext numbers as decimal strings (< n^2).
    """
    entries = []
    for cid in cids:
        bit = 1 if cid == chosen else 0
        c = str(pub.encrypt(bit).ciphertext())
        entries.append({"candidate_id": cid, "c": c})
    return {
        "scheme": "paillier-1hot",
        "key_id": f"paillier-{__key_id(pub)}",
        "exponent": 0,
        "entries": entries,
    }

def test_e2ee_accepts_and_stores_ciphertexts(app, client):
    _login(client)
    cids = ["c1", "c2", "c3"]
    ballot = _build_ballot(app._pub, cids, chosen="c2")
    payload = {
        "election_id": "election_demo",
        "token": "tkn",
        "signature": "sig",
        "ballot": ballot,
    }
    r = client.post("/cast-vote", data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200, r.data

    # server should have stored 1 row per candidate with exponent=0 and big integer ciphertext
    stored = app._added
    assert len(stored) == len(cids)
    for row in stored:
        assert row.election_id == "election_demo"
        assert row.vote_exponent == 0
        # decimal string parses; and < n^2
        v = int(row.vote_ciphertext)
        assert isinstance(v, int)
        assert v < int(app._pub.n) ** 2

def test_reject_wrong_scheme(app, client):
    _login(client)
    ballot = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    ballot["scheme"] = "not-supported"
    payload = {"election_id": "E", "token": "t", "signature": "s", "ballot": ballot}
    r = client.post("/cast-vote", data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 400
    assert b"unsupported_ballot_scheme" in r.data

def test_reject_length_mismatch(app, client):
    _login(client)
    b = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    b["entries"] = b["entries"][:-1]  # remove one
    r = client.post("/cast-vote", data=json.dumps({"election_id":"E","token":"t","signature":"s","ballot":b}),
                    content_type="application/json")
    assert r.status_code == 400
    assert b"ballot_length_mismatch" in r.data

def test_reject_duplicate_candidate_ids(app, client):
    _login(client)
    b = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    b["entries"][1]["candidate_id"] = "c1"  # duplicate
    r = client.post("/cast-vote", data=json.dumps({"election_id":"E","token":"t","signature":"s","ballot":b}),
                    content_type="application/json")
    assert r.status_code == 400
    assert b"invalid_candidate_in_ballot" in r.data

def test_reject_non_integer_ciphertext(app, client):
    _login(client)
    b = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    b["entries"][0]["c"] = "not-an-int"
    r = client.post("/cast-vote", data=json.dumps({"election_id":"E","token":"t","signature":"s","ballot":b}),
                    content_type="application/json")
    assert r.status_code == 400
    assert b"ciphertext_not_integer" in r.data

def test_reject_ciphertext_out_of_range(app, client):
    _login(client)
    b = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    b["entries"][0]["c"] = str(int(app._pub.n) ** 2)  # >= n^2
    r = client.post("/cast-vote", data=json.dumps({"election_id":"E","token":"t","signature":"s","ballot":b}),
                    content_type="application/json")
    assert r.status_code == 400
    assert b"ciphertext_out_of_range" in r.data

def test_reject_key_id_mismatch(app, client):
    _login(client)
    b = _build_ballot(app._pub, ["c1", "c2", "c3"], "c1")
    b["key_id"] = "paillier-deadbeef"  # wrong
    r = client.post("/cast-vote", data=json.dumps({"election_id":"E","token":"t","signature":"s","ballot":b}),
                    content_type="application/json")
    assert r.status_code == 400
    assert b"paillier_key_mismatch" in r.data
