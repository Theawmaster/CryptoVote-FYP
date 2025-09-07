# routes/wbb.py
from flask import Blueprint, jsonify, request
from models.db import db
from models.wbb_entry import WbbEntry
from utilities.merkle import merkle_root, merkle_proof

wbb_bp = Blueprint("wbb", __name__)

@wbb_bp.get("/wbb/<election_id>")
def wbb_list(election_id: str):
    # Optional: narrow by tracker for a compact per-voter view
    tracker = request.args.get("tracker")

    base_q = db.session.query(WbbEntry)\
        .filter_by(election_id=election_id)\
        .order_by(WbbEntry.position.asc())

    if tracker:
        items = base_q.filter(WbbEntry.tracker == tracker).all()
    else:
        items = base_q.all()

    # Build root over the FULL set for this election
    all_entries = base_q.all() if tracker else items
    if tracker:
        # If filtered, we still need the full set for an accurate root:
        all_entries = db.session.query(WbbEntry)\
            .filter_by(election_id=election_id)\
            .order_by(WbbEntry.position.asc())\
            .all()

    leaves = [e.leaf_hash for e in all_entries]
    root = merkle_root(leaves)

    return jsonify({
        "election_id": election_id,
        "count": len(all_entries),
        "root": root,
        "items": [
            {
                "index": e.position,
                "tracker": e.tracker,
                "commitment_hash": getattr(e, "commitment_hash", None),
                "leaf_hash": e.leaf_hash,
                "published_at": int(e.created_at.timestamp()),
            } for e in items
        ]
    }), 200


@wbb_bp.get("/wbb/<election_id>/proof")
def wbb_proof(election_id: str):
    tracker = request.args.get("tracker")
    token_hash = request.args.get("token_hash")

    if not tracker and not token_hash:
        return jsonify({"error": "provide tracker or token_hash"}), 400

    entries = db.session.query(WbbEntry)\
        .filter_by(election_id=election_id)\
        .order_by(WbbEntry.position.asc())\
        .all()

    if not entries:
        return jsonify({"found": False, "count": 0}), 200

    # find target index
    idx = -1
    for i, e in enumerate(entries):
        if tracker and e.tracker == tracker:
            idx = i; break
        if token_hash and e.token_hash == token_hash:
            idx = i; break

    leaves = [e.leaf_hash for e in entries]
    root = merkle_root(leaves)

    if idx == -1:
        return jsonify({
            "found": False,
            "count": len(entries),
            "root": root
        }), 200

    e = entries[idx]
    return jsonify({
        "found": True,
        "entry": {
            "election_id": e.election_id,
            "tracker": e.tracker,
            "commitment_hash": getattr(e, "commitment_hash", None),
            "index": e.position,
            "leaf_hash": e.leaf_hash,
            "merkle_path": merkle_proof(leaves, idx),
            "root": root,
            "root_sig": None,  # fill later if you sign roots
            "published_at": int(e.created_at.timestamp()),
        }
    }), 200
