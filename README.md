# CryptoVote: Cryptographic Electronic Voting System (NTU FYP)

**CryptoVote** is a secure, privacy-preserving e-voting prototype developed at **Nanyang Technological University (NTU)**, Singapore.  
It integrates **blind signatures**, **homomorphic encryption**, and a **public Web Bulletin Board (WBB)** to ensure verifiable and anonymous elections.

> ⚠️ Research prototype for academic purposes — *not intended for national deployments.*

---

## Objectives
- Achieve **privacy** and **verifiability** through principled cryptography.  
- Prevent **impersonation**, **replay**, and **tampering**.  
- Support **end-to-end verifiability** with blind-signed tokens and WBB proofs.  
- Enable **homomorphic tallying** (Paillier) without exposing plaintext votes.  
- Preserve **integrity** via single-use tokens and Merkle-root audit trails.

---

## Core Security Design

| Pillar | Implementation Highlights |
|--------|----------------------------|
| **Confidentiality** | Client-side Paillier encryption (one-hot vector per ballot) |
| **Authenticity** | RSA digital signatures, TOTP 2FA, signed nonces |
| **Anonymity** | Blind-signed per-election tokens decouple voter identity |
| **Integrity** | Single-use tokens, Merkleized WBB, audit logs |
| **Auditability** | Inclusion proofs, downloadable CSV/PDF audit bundles |

---

## ⚙️ Architecture Overview

### Voter Flow
1. **Login + 2FA** → obtain signed nonce.  
2. **Claim blind token** → server blind-signs a client-generated token.  
3. **Encrypt vote** → client encrypts a one-hot vector using Paillier public key.  
4. **Cast vote** → submit `{ election_id, signed_token, tracker, ciphertexts }`.  
5. **Verify** → check tracker on WBB via `/proof?tracker=...`.

### Admin Flow
- Create/start/end elections.  
- Generate **homomorphic tally**, publish signed WBB root + audit bundle.  

---

## Tech Stack

| Layer | Technology |
|-------|-------------|
| **Frontend** | React + TypeScript, Tailwind, Framer Motion |
| **Backend** | Flask (Python), SQLAlchemy, Redis (rate-limiting) |
| **Crypto** | `phe` (Paillier), `PyCryptodome`, `PyOTP` |
| **Database** | PostgreSQL (UTC stored, SGT rendered) |
| **Reports** | CSV & PDF (ReportLab / FPDF) |

---

## Data Model (key tables)

- `elections (id, name, start_time, end_time, tally_generated, …)`  
- `candidates (id, name, election_id)`  
- `issued_tokens (token_hash, election_id, issued_at)` — **unique per election**  
- `encrypted_candidate_votes (candidate_id, token_hash, ciphertext, election_id)` — **unique per token**  
- `wbb_entries (election_id, tracker, token_hash, leaf_hash, position)` — **Merkle root inclusion**

---

## Setup

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
flask run  # default: http://127.0.0.1:5000

# Frontend
cd frontend
npm ci
npm run dev
```

---

## Testing

```bash
# Backend
pytest -q

# Frontend
npm test -- --coverage
```

> Integration tests use an in-memory SQLite DB and mock Paillier keys.

---

## DDoS / Abuse Prevention

Flask-Limiter (Redis-backed) protects key routes:

| Endpoint Type | Limit | Example |
|----------------|--------|----------|
| Auth (login/2FA) | 5/sec · 60/min | `/login`, `/2fa-verify` |
| Cast-vote | 3/sec · 30/min | `/cast-vote` |
| Read (WBB, results) | 30/sec · 600/min | `/wbb/:id` |
| Default | 200/min | global fallback |

> Excess traffic triggers **HTTP 429** before DB work.

---

## Tally & Audit

Homomorphic tallying computes:
- **total_cast**, **unique_tokens**, **valid_tokens**  
- Deduplicates and excludes unissued tokens.  
- Publishes per-candidate ciphertext sums and signed WBB root.

---

## Roadmap

- Migrate signatures to **ECDSA (P-256)** for reduced key size.  
- Implement **client-side Merkle proof viewer**.  
- Add **fuzz tests** for concurrent token issuance.  

---

## License & Credits

Released under **AGPL-3.0**.  
Developed as an NTU Final Year Project — *CryptoVote* (2025).

**Author:** Alvin Aw Yong  
[aavyong001@e.ntu.edu.sg](mailto:aavyong001@e.ntu.edu.sg)  
[LinkedIn](https://www.linkedin.com/in/alvin-aw-yong-3087591a6)
