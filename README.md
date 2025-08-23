# CryptoVote – Cryptographic Electronic Voting System (NTU FYP)

**CryptoVote** is a secure, privacy-preserving e-voting prototype developed at Nanyang Technological University (NTU), Singapore.  
It weaves **digital signatures**, **blind signatures**, and **homomorphic encryption** into a full election lifecycle—privacy kept, verifiability earned.

> ⚠️ Research prototype for education. **Not** for governmental deployments.

---

## Objectives

- Ensure **privacy** and **verifiability** with principled cryptography  
- Prevent **manipulation**, **impersonation**, and **replay**  
- Deliver **end-to-end verifiability** (blind-signed eligibility + 2FA)  
- Enable **anonymous yet auditable** homomorphic tallying  
- Preserve **integrity** with traceable logs and proofs

---

## What’s New (Aug 2025)

**Election-scoped token model & replay defense**

- **One voter, one token, one vote (per election).**  
  Tokens are now explicitly **scoped to an election** and **single-use** by design.

- **Replay prevention (DB-level).**  
  Unique index on `encrypted_candidate_votes.token_hash` guarantees one counted ballot per token.  

- **Issued-token provenance.**  
  `issued_tokens` includes `election_id`; cast-time validation now requires a matching `(token_hash, election_id)` pair.

- **Tally diagnostics (transparent by default).**  
  Reports distinguish:  
  `total_cast`, `unique_tokens`, `valid_tokens`, `duplicates`, `unissued_or_mismatched`.

- **ZKP tally alignment.**  
  ZKP pipeline now tallies **only** first-per-token **and** only tokens that were **actually issued for this election**.

> In dev, reusing the same account previously produced multiple ballots by reissuing tokens.  
> With the new guards, production nets to **one counted vote per account** (per election).

---

## Core Security Pillars

| Pillar              | Implementation Highlights                                                                 |
|---------------------|--------------------------------------------------------------------------------------------|
| **Confidentiality** | Paillier Homomorphic Encryption (client encrypts before transport)                         |
| **Authenticity**    | Digital Signatures (RSA/ECDSA) + TOTP (2FA) + server nonce challenge                       |
| **Anonymity**       | Blind-signed token issuance decouples identity from ballot                                 |
| **Integrity**       | Single-use tokens, replay-proof inserts, admin action hash-chains                          |
| **Auditability**    | ZK proofs, CSV/PDF artifacts, explicit tally diagnostics, timestamped trails               |

---

## Tech Stack

| Layer          | Technology                                                                 |
|----------------|-----------------------------------------------------------------------------|
| **Frontend**   | React + TypeScript, Tailwind CSS, React Router v6, Framer Motion            |
| **Backend**    | Flask (Python), SQLAlchemy                                                  |
| **Crypto**     | `PyCryptodome`, `phe` (Paillier), `PyOTP`                                   |
| **Database**   | PostgreSQL (UTC storage; SGT rendering in UI)                               |
| **Reports**    | CSV + **FPDF** (PDF), Jinja2 templates                                      |

---

## Data Model (key tables)

- **elections** `(id, name, rsa_key_id, start_time, end_time, is_active, has_started, has_ended, tally_generated, created_at, updated_at)`
- **candidates** `(id, name, election_id [FK→elections])`
- **issued_tokens** `(token_hash, election_id [FK→elections], issued_at, …)`  
  **Unique:** `(token_hash, election_id)`
- **encrypted_candidate_votes** `(id, candidate_id [FK→candidates], token_hash, vote_ciphertext, vote_exponent, cast_at)`  
  **Unique:** `token_hash`

> Minimal linkage preserves anonymity: voters are not linked to tokens or ballots.

---

## Protocol Flows

### Voter Flow

1. **Register** → `POST /register`  
   Verify NTU email via link → TOTP QR shown

2. **Authenticate** → `POST /login` (returns nonce) → client signs & returns

3. **2FA** → `POST /2fa-verify` (TOTP)

4. **Claim Blind Token** → `POST /claim-token`  
   Client sends *blinded* token → server returns *blind-signed* token

5. **Cast Vote** → `POST /cast-vote`  
   Client encrypts 0/1 vector per candidate with Paillier; includes **unblinded signed token**.  
   Backend validates `(token_hash, election_id)` and inserts ballot (replay-proof).

### Admin Flow

- **Start** → `POST /admin/start-election/:id`  
- **Status** → `GET /admin/election-status/:id`  
- **End** → `POST /admin/end-election/:id`  
- **Tally** → `POST /admin/tally-election/:id` (homomorphic sum + ZKPs)  
- **Audit** → `GET /admin/audit-report/:id?format=csv|pdf`  
- **Verify** → `GET /admin/verify-proof`

---

## Tally & Audit Invariants

The report prints:

- `total_cast` – raw rows in `encrypted_candidate_votes` for the election  
- `unique_tokens` – first-per-token ballots (deduped)  
- `valid_tokens` – deduped **AND** backed by `issued_tokens(election_id)`  
- `duplicates = total_cast - unique_tokens`  
- `unissued_or_mismatched = unique_tokens - valid_tokens`

Only **valid_tokens** contribute to per-candidate tallies and ZKPs.

---

## API Surface (selected)

```http
POST /register
GET  /verify-email?token=...

POST /login                # returns { nonce }
POST /2fa-verify
POST /claim-token
POST /cast-vote

POST /admin/start-election/:id
GET  /admin/election-status/:id
POST /admin/end-election/:id
POST /admin/tally-election/:id
GET  /admin/audit-report/:id?format=csv|pdf
GET  /admin/verify-proof
```

**Errors** return `{ code, message, retryAfterMs? }`.

---

## Frontend Guide (experience notes)

- **Aesthetic.** Minimal, dark-first; motion signals milestones, not decoration.  
- **Trust cues.** Signature previews; success toasts for key steps; explicit “what was stored”.  
- **Crypto in browser.** Keys & nonces in IndexedDB (`CryptoVoteDB`, `cryptoVoteKeys`); no ballots cached.  
- **Accessibility.** High-contrast focus rings; honors `prefers-reduced-motion`.

**Route skeleton**
```tsx
<AnimatePresence mode="wait">
  <Routes>
    <Route path="/" element={<OnboardingLanding />} />
    <Route path="/onboarding/1" element={<Onboarding1 />} />
    <Route path="/onboarding/2" element={<Onboarding2 />} />
    <Route path="/onboarding/3" element={<Onboarding3 />} />
    <Route path="/onboarding/4" element={<Onboarding4 />} />
    <Route path="/auth/voter" element={<VoterAuth />} />
  </Routes>
</AnimatePresence>
```

**Dev cleanup (for testing)**
```js
indexedDB.deleteDatabase('CryptoVoteDB');
indexedDB.deleteDatabase('cryptoVoteKeys');
```

---

## Setup & Development

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=cryptovote/backend/app.py
flask run

# Frontend
npm ci
npm run dev
```

### Testing

```bash
# Backend
PYTHONPATH=. pytest --cov=cryptovote/backend cryptovote/backend/tests/ -v

# Frontend
npm run typecheck && npm run lint && npm test
```

---

## Migration Snippets (DB hardening)

```sql
-- 1) Scope tokens to elections
ALTER TABLE issued_tokens ADD COLUMN IF NOT EXISTS election_id varchar(64);
UPDATE issued_tokens t
SET election_id = '<backfill_election_id>'  -- one-off backfill per issuance log
WHERE election_id IS NULL;

ALTER TABLE issued_tokens
  ALTER COLUMN election_id SET NOT NULL;

ALTER TABLE issued_tokens
  ADD CONSTRAINT fk_tokens_election
  FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE;

-- 2) Enforce single-use tokens
CREATE UNIQUE INDEX IF NOT EXISTS ux_issued_tokens_token_election
  ON issued_tokens(token_hash, election_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_votes_token_hash
  ON encrypted_candidate_votes(token_hash);
```

> Store timestamps in UTC; render in **Asia/Singapore (SGT)** in UI/admin.

---

## Current Status (Aug 2025)

- **Voter onboarding & auth** – complete (email verify, nonce sign, TOTP)  
- **Blind-token issuance & cast** – functional with replay-proof insert  
- **Admin console** – start/end/tally/audit stable  
- **Reports** – CSV/PDF with diagnostics; ZKPs aligned to valid tokens

**Near-term roadmap:** inline proof viewer, richer admin audit trails, CLI verifier, fuzz tests for token issuance & casting race conditions.

---

## License & Credits

Released under **AGPL-3.0**. Contributions welcome—please keep the spirit of verifiable, privacy-first systems.

**Project**: CryptoVote — NTU, Singapore  
**Author**: Alvin Aw Yong • [LinkedIn](https://www.linkedin.com/in/alvin-aw-yong-3087591a6) • [Email](mailto:aavyong001@e.ntu.edu.sg)
