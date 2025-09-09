# CryptoVote – Cryptographic Electronic Voting System (NTU FYP)

**CryptoVote** is a secure, privacy‑preserving e‑voting prototype developed at Nanyang Technological University (NTU), Singapore.  
It weaves **blind signatures**, **homomorphic encryption**, and a **public Web Bulletin Board (WBB)** into a verifiable election workflow.

> ⚠️ Research prototype for education. **Not** for governmental deployments.

---

## Objectives

- Ensure **privacy** and **verifiability** with principled cryptography.  
- Prevent **manipulation**, **impersonation**, and **replay**.  
- Deliver **end‑to‑end verifiability** (blind‑signed eligibility + WBB inclusion proofs).  
- Enable **anonymous yet auditable** homomorphic tallying (Paillier).  
- Preserve **integrity** with single‑use tokens, Merkle roots, and explicit diagnostics.

---

## What’s New (Aug–Sep 2025)

### End‑to‑End (client‑side) encryption
- Ballots are encrypted **in the browser** as a Paillier **one‑hot** vector (0/1 per candidate) and sent as ciphertexts only.
- Server stores ciphertext per candidate and never sees the choice in plaintext.

### Web Bulletin Board (WBB)
- Every accepted ballot appends a **tracker** entry (random hex chosen by the client).  
- WBB exposes a **Merkle root** and **inclusion proofs** (`/wbb/:election_id/proof?tracker=...`).  
- Voters verify their tracker is included **without revealing** who they voted for.

### Election‑scoped tokens & replay defense
- Tokens are **blind‑signed** and **scoped to one election**.
- DB constraints enforce **single‑use** per election.

### Application‑layer DDoS protection
- **Redis‑backed rate limiting** via Flask‑Limiter:
  - Login/auth: **5/sec; 60/min** per IP
  - Cast‑vote (mutating): **3/sec; 30/min** per IP
  - Read API (results/WBB): **30/sec; 600/min** per IP
  - Default: **200/min**
- Attack traffic gets **HTTP 429** before DB work, protecting capacity.

> ℹ️ **Planned**: migrate server authentication signatures to **ECDSA (P‑256)**.  
> Blind‑signature issuance currently uses RSA‑based blinding; moving to EC blind signatures (e.g., Schnorr‑style) will be evaluated separately.

---

## Core Security Pillars

| Pillar              | Implementation Highlights                                                                 |
|---------------------|--------------------------------------------------------------------------------------------|
| **Confidentiality** | Paillier Homomorphic Encryption (client encrypts before transport)                         |
| **Authenticity**    | Digital signatures (currently RSA; planned ECDSA), TOTP 2FA, signed nonces                 |
| **Anonymity**       | **Blind‑signed** per‑election tokens decouple identity from ballot                         |
| **Integrity**       | Single‑use tokens, unique DB constraints, Merkleized WBB, audit logs                       |
| **Auditability**    | Inclusion proofs, downloadable **audit bundles**, CSV/PDF reports                          |

---

## Tech Stack

| Layer          | Technology                                                                 |
|----------------|-----------------------------------------------------------------------------|
| **Frontend**   | React + TypeScript, React Router, Tailwind, Framer Motion                  |
| **Backend**    | Flask (Python), SQLAlchemy                                                  |
| **Crypto**     | `phe` (Paillier), `PyCryptodome`, `PyOTP`                                   |
| **Database**   | PostgreSQL (UTC in DB; SGT rendered)                                        |
| **Reports**    | ReportLab / FPDF for PDF; CSV; Jinja2                                      |
| **Infra**      | Flask‑Limiter + Redis for rate limiting                                     |

---

## Data Model (selected)

- **elections** `(id, name, rsa_key_id, start_time, end_time, is_active, has_started, has_ended, tally_generated, created_at, updated_at)`  
- **candidates** `(id, name, election_id [FK→elections])`  
- **issued_tokens** `(token_hash, election_id [FK→elections], issued_at, …)` **UNIQUE** `(token_hash, election_id)`  
- **encrypted_candidate_votes** `(id, candidate_id [FK→candidates], token_hash, vote_ciphertext, vote_exponent, election_id, cast_at)`  
  - **UNIQUE** `(election_id, token_hash)`  
  - **INDEX** `(election_id, candidate_id)`  
- **wbb_entries** `(id, election_id, tracker, token_hash, position, leaf_hash, commitment_hash?, created_at)`  
  - **UNIQUE** `(election_id, token_hash)` and `(election_id, position)`

> Minimal linkage preserves anonymity: voters are never linked to tokens or ballots.

---

## Protocol Flows (high level)

### Voter
1. **Login + 2FA** → server issues a signed **nonce** challenge.  
2. **Claim blind token** → client blinds random token; server blind‑signs; client unblinds (server never sees token).  
3. **Open ballot** → frontend fetches Paillier public key, encrypts a 0/1 one‑hot vector.  
4. **Cast** → send `{ election_id, signed_token, tracker, encrypted ballot }`.  
5. **Verify** → copy tracker; check `/wbb/:election_id/proof?tracker=...` for inclusion; download receipt/audit bundle.

### Admin
- Start/end election, homomorphic **tally**, publish audit bundle (ciphertexts + Merkle root + summaries), and sign final root.

---

## Setup & Development

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=cryptovote/backend/app.py
flask run  # default http://127.0.0.1:5000 or your configured port

# Frontend
cd frontend
npm ci
npm run dev   # Vite/React dev server
```

---

## How to Run the Tests

### Backend (unit/integration)
> **Run from the backend directory.**
```bash
pytest -q                              # run all tests
pytest -q tests/test_keys_endpoint.py  # run a specific file
```
- Uses **Flask test client**, **in‑memory SQLite**, and **monkey‑patched Paillier test keys**.

### Frontend (unit)
> **Run from the frontend directory.**
```bash
npm test -- --coverage src/lib/__tests__/cred.random.test.ts  # run a specific file with coverage
```
- Uses **Jest + React Testing Library**; network **fetch is mocked**.

### End‑to‑End (optional)
```bash
# start backend + frontend (dev)
npm run dev:stack     # or start each side in separate terminals

# then run e2e
npm run e2e           # Cypress or Playwright (see package.json)
```

---

## DDoS / Abuse‑Prevention (Layer‑7)

### What is enforced
- **Shared buckets** (per IP by default, redis‑backed):
  - **auth** (login/2fa): `5/sec; 60/min`
  - **mutate** (cast‑vote, state‑changing): `3/sec; 30/min`
  - **read** (results/WBB): `30/sec; 600/min`
  - **default**: `200/min`
- Violators get **HTTP 429** (Too Many Requests) without DB hits.

### How to demo the protection
Requires [`wrk`](https://github.com/wg/wrk). We ship a helper script:

```bash
./flood.sh http://127.0.0.1:5010/login
```

What it does:
- Sends many **POST** requests to `/login` from a fixed “fake IP” header.  
- You’ll see a high percentage of **429** responses once the quota is hit.  
- The app stays responsive; the DB stays calm.

> Production note: For truly massive network floods, put a **CDN/WAF** (Cloudflare/AWS Shield) in front. App‑level limits are your **last line**.

---

## Tally & Audit Invariants

The tally pipeline explicitly separates and reports:
- `total_cast` – raw rows for the election.  
- `unique_tokens` – deduped first‑per‑token ballots.  
- `valid_tokens` – deduped **and** backed by `issued_tokens(election_id)`.
- `duplicates = total_cast - unique_tokens`.  
- `unissued_or_mismatched = unique_tokens - valid_tokens`.

Only **valid_tokens** contribute to per‑candidate homomorphic sums and proofs.

---

## API (selected)

```http
POST /register
GET  /verify-email?token=...

POST /login                 # returns { nonce }
POST /2fa-verify

POST /claim-token           # blind-sign flow
POST /cast-vote             # accepts encrypted one-hot ballots + signed token + tracker

GET  /results/:election_id
GET  /wbb/:election_id
GET  /wbb/:election_id/proof?tracker=...

POST /admin/start-election/:id
POST /admin/end-election/:id
POST /admin/tally-election/:id
GET  /admin/audit-bundle/:id
```

Errors are JSON: `{ error, detail?, retryAfterMs? }`.

---

## Migration Snippets (DB hardening)

```sql
-- Enforce single-use tokens per election
CREATE UNIQUE INDEX IF NOT EXISTS ux_votes_eid_token
  ON encrypted_candidate_votes (election_id, token_hash);

-- Speed up tallying per election
CREATE INDEX IF NOT EXISTS ix_votes_eid_cid
  ON encrypted_candidate_votes (election_id, candidate_id);

-- WBB uniqueness per election
CREATE UNIQUE INDEX IF NOT EXISTS ux_wbb_eid_pos
  ON wbb_entries (election_id, position);

CREATE UNIQUE INDEX IF NOT EXISTS ux_wbb_eid_tokenhash
  ON wbb_entries (election_id, token_hash);
```

---

## Frontend Notes

- **No plaintext ballots** persist in storage; only the temporary credential is kept in `sessionStorage` during the voting session.  
- **Voter Landing** includes:
  - Results lookup + audit bundle download
  - **WBB verification** by tracker
  - Session timeout notice (2‑minute inactivity reminder)

---

## Roadmap / Pending Work

- 🔁 **ECDSA migration** for server authentication signatures (nonce/WBB root signing) to reduce key sizes and latency.  
  - Blind‑signature issuance remains RSA for now; evaluate EC‑Schnorr blind signatures next.
- 📄 Inline proof viewer (client‑side Merkle verification UI).
- 🧪 Fuzz tests for token issuance & concurrent cast edge cases.
- 🛡️ Optional: per‑session or per‑account rate limits in addition to per‑IP for NAT fairness.

---

## License & Credits

Released under **AGPL‑3.0**. Contributions welcome—please keep the spirit of verifiable, privacy‑first systems.

**Project**: CryptoVote — NTU, Singapore  
**Author**: Alvin Aw Yong • LinkedIn: https://www.linkedin.com/in/alvin-aw-yong-3087591a6 • Email: aavyong001@e.ntu.edu.sg
