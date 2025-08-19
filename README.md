# CryptoVote – Cryptographic Electronic Voting System (NTU FYP)

**CryptoVote** is a secure, privacy-preserving e-voting prototype developed as a Final Year Project (FYP) at Nanyang Technological University (NTU), Singapore.  
It integrates advanced cryptographic techniques such as **digital signatures**, **blind signatures**, and **homomorphic encryption**, covering the **full election lifecycle**.

> ⚠️ For educational and research use only. Not suitable for real-world governmental deployments.

---

## Objectives

- Ensure **privacy** and **verifiability** using cryptographic constructs  
- Prevent vote manipulation, coercion, and impersonation  
- Support **end-to-end verifiability** with blind signatures and 2FA  
- Enable **anonymous** yet **auditable** homomorphic vote tallying  
- Provide traceable logs and proofs for **election integrity**

---

## Core Security Pillars

| Pillar              | Implementation Highlights                                                       |
|---------------------|----------------------------------------------------------------------------------|
| **Confidentiality** | Paillier Homomorphic Encryption ensures votes stay secret                        |
| **Authenticity**    | Digital Signature (RSA/ECDSA) + OTP (2FA) + Voter Nonce                          |
| **Anonymity**       | Blinded Token issuance breaks voter–vote linkage                                |
| **Auditability**    | ZKPs for vote proof, CSV/PDF logs, and election trail                           |
| **Integrity**       | Database-stored timestamps, token reuse prevention, admin action logging        |

---

## Tech Stack

| Layer         | Technology                                                                 |
|---------------|-----------------------------------------------------------------------------|
| **Frontend**  | React.js + TypeScript, Framer Motion, Tailwind CSS, React Router v6         |
| **Backend**   | Flask (Python)                                                              |
| **Cryptography** | `PyCryptodome`, `phe` (Paillier), `PyOTP`                                 |
| **Auth**      | RSA / ECDSA Digital Signatures, Blind Signatures                            |
| **Database**  | PostgreSQL + pgAdmin                                                         |
| **Reports**   | PDFKit (wkhtmltopdf), CSV, Flask Templates                                   |

---

## System Architecture

### Voter Operation Flow

1. **Register Account**
   ```
   POST /register
   ```
   - Input NTU email → system sends verification link

2. **Email Verification**
   ```
   GET /verify-email?token=...
   ```
   - Email confirmed → OTP QR code issued (via PyOTP)

3. **Authenticate with Digital Signature**
   ```
   POST /login
   ```
   - Server returns a nonce → user signs it → sends back with request

4. **OTP Verification**
   ```
   POST /2fa-verify
   ```
   - Verifies OTP from authenticator app (TOTP)

5. **Receive Blinded Token**
   ```
   POST /claim-token
   ```
   - User submits a blinded token → receives RSA-signed blind token

6. **Vote**
   ```
   POST /cast-vote
   ```
   - Encrypted 0/1 vote cast per candidate with signed token
   - Votes stored in `encrypted_candidate_votes` table
   - Tokens marked as used in `issued_tokens`

---

### Admin Operation Flow

1. **Start Election**
   ```
   POST /admin/start-election/<election_id>
   ```

2. **Monitor Election**
   ```
   GET /admin/election-status/<election_id>
   ```

3. **End Election**
   ```
   POST /admin/end-election/<election_id>
   ```

4. **Tally Votes**
   ```
   POST /admin/tally-election/<election_id>
   ```
   - Homomorphic vote tallying using Paillier
   - ZKPs generated for verification

5. **Audit Result**
   ```
   GET /admin/audit-report/<election_id>
   ```

6. **Download Report**
   ```
   GET /admin/download-report/<election_id>?format=csv/pdf
   ```

7. **Verify ZKP**
   ```
   GET /admin/verify-proof
   ```

8. **Remove PEM cache on browser**
   ```
   indexedDB.deleteDatabase('CryptoVoteDB'); // Do it on console dev tools
   indexedDB.deleteDatabase('cryptoVoteKeys');
   ```

---

# CryptoVote – Frontend Guide
*A humane interface for cryptographic trust*

CryptoVote’s frontend is the story layer of your election: the place where cryptography feels effortless and voting feels safe. Instead of a checklist of toggles and endpoints, this document explains how the interface flows, how it thinks about state, and how it earns trust with motion, clarity, and restraint.

> ⚠️ Built for education and research (NTU FYP). Not intended for real-world governmental use.

---

## Why this frontend exists

E‑voting fails when users hesitate. The UI must carry heavy cryptography lightly—explaining just enough, guiding decisively, never revealing identity, and always confirming integrity. Every screen is crafted to reassure: privacy by default, verification without friction, and a clear path from onboarding to verifiable tally.

---

## The experience at a glance

- **Tone & aesthetic.** Minimalist, dark‑first palette with purposeful contrast; motion used to signify state changes, not to decorate.
- **Navigation.** A linear, low‑cognitive‑load journey for voters; a command console for admins.
- **Trust cues.** Explicit confirmations, signed actions, and reversible safe exits before commitment.
- **Resilience.** Optimistic UI with rigorous rollback when cryptographic verification fails.

---

## Architecture (frontend focus)

**Stack.** React + TypeScript, React Router v6, Tailwind CSS, Framer Motion.  
**Backends spoken.** Flask API for auth, token issuance, vote casting, and tally.  
**Crypto in the browser.** Key handling via IndexedDB with careful lifetime rules; signatures happen client‑side, encryption happens before transport.

```tsx
<AnimatePresence mode="wait">
  <Routes location={location} key={location.pathname}>
    <Route path="/" element={<OnboardingLanding />} />
    <Route path="/onboarding/1" element={<Onboarding1 />} />
    <Route path="/onboarding/2" element={<Onboarding2 />} />
    <Route path="/onboarding/3" element={<Onboarding3 />} />
    <Route path="/onboarding/4" element={<Onboarding4 />} />
    <Route path="/auth/voter" element={<VoterAuth />} />
  </Routes>
</AnimatePresence>
```

**State model.** Local UI state (React), persistent secrets in IndexedDB (`CryptoVoteDB`, `cryptoVoteKeys`), session hints via cookies; no ballots or tokens are cached beyond need.

---

## User journeys

### Voter journey — from curiosity to cast

1. **Register** → Provide NTU email; receive a verification link.  
   `POST /register` → `GET /verify-email?token=…`  
   On success, the app displays a TOTP QR code and stores public‑key metadata locally.

2. **Authenticate** → Challenge–response with the server‑issued nonce.  
   `POST /login` (returns a nonce) → user signs → resubmit.

3. **Second factor** → Enter TOTP.  
   `POST /2fa-verify` validates the time‑based OTP.

4. **Claim anonymity** → Obtain a blind‑signed token.  
   `POST /claim-token` with blinded token → receive server signature (still blinded).

5. **Cast** → Encrypt and submit one 0/1 vote per candidate.  
   `POST /cast-vote` writes encrypted vectors; token is marked as spent.

All sensitive transitions carry **motion affordances** (subtle fade/slide) and **explicit confirmations** (what was signed, what was stored, what remains only client‑side).

### Admin journey — steward the election, don’t touch the ballots

- **Start** `POST /admin/start-election/<id>`  
- **Observe** `GET /admin/election-status/<id>` (live counts without revealing votes)
- **End** `POST /admin/end-election/<id>`  
- **Tally** `POST /admin/tally-election/<id>` → homomorphic tally, plus ZK proofs  
- **Audit** `GET /admin/audit-report/<id>` → CSV/PDF downloads
- **Verify** `GET /admin/verify-proof`

The admin UI presents a compact ledger: timestamps, actor, action hash chain, and proof artifacts. No ability to deanonymize; only verifiable procedures.

---

## Security‑by‑design in the UI

| Goal | Frontend behaviour |
|---|---|
| **Confidentiality** | Encrypt before transit; never render decrypted ballots; wipe volatile keys on logout. |
| **Authenticity** | Client‑side signing of server nonces; surfaced signature previews before send. |
| **Anonymity** | Blind‑signed token flow decouples identity from casting; UI keeps identity screens and ballot screens in separate trees. |
| **Integrity** | Idempotent actions; token reuse detection with clear error recovery; admin actions chained with visible hashes. |
| **Auditability** | Downloadable artifacts (CSV/PDF) and a “verify again” button that replays checks without re‑fetching raw ballots. |

---

## Theming & interaction

- **Dark mode** by default, light mode opt‑in; preference persisted.  
- **Motion** via Framer Motion’s `AnimatePresence`—only on route changes and cryptographic milestones.  
- **Responsiveness**: grid‑first, fluid typography, touch targets ≥44px.  
- **Accessibility**: focus rings on all interactive elements, semantic landmarks, reduced‑motion honouring via `prefers-reduced-motion`.

---

## API contracts (frontend expectations)

```http
POST /register
POST /login            # returns { nonce }
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

Error payloads should include machine‑readable `code`, user‑friendly `message`, and optional `retryAfterMs` for rate limiting.

---

## Data & storage

- **IndexedDB**: `CryptoVoteDB`, `cryptoVoteKeys` (PEMs, nonces, ephemeral flags).  
- **Cleanup** (for test/dev):  
  ```js
  indexedDB.deleteDatabase('CryptoVoteDB');
  indexedDB.deleteDatabase('cryptoVoteKeys');
  ```
- **No PII** or ballot content rendered post‑submission.

---

## Development workflow

```bash
# install
npm ci

# run
npm run dev

# typecheck & lint
npm run typecheck && npm run lint

# build
npm run build
```

**Testing (frontend):**  
Snapshot renders of onboarding/auth, route transition tests, validation of OTP inputs, and interaction contracts around nonce signing and token claims.

**Testing (backend, from project root):**
```bash
PYTHONPATH=. pytest --cov=cryptovote/backend cryptovote/backend/tests/ -v
```

---

## Current status (Aug 2025)

- **Onboarding** (`/`, `/onboarding/1–4`) — complete, with motion and dark mode.  
- **Voter Auth** (`/auth/voter`) — functional; modal layering polish in progress.  
- **Admin console** — stable for start/end/tally/audit flows.

Roadmap (UI polish): inline proof viewers, progressive disclosures for crypto explanations, and error‑state illustrations that make recovery intuitive.

---

## License & credits

Released under **AGPL‑3.0**. By using or modifying this interface, you agree to share improvements to benefit the research community.

**Project:** CryptoVote — NTU, Singapore  
**Author:** Alvin Aw Yong • [LinkedIn](https://www.linkedin.com/in/alvin-aw-yong-3087591a6) • [Email](mailto:aavyong001@e.ntu.edu.sg)
