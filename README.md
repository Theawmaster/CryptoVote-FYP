# CryptoVote – Cryptographic Electronic Voting System (NTU FYP)

**CryptoVote** is a secure, privacy-preserving e-voting prototype developed for the Final Year Project (FYP) at Nanyang Technological University (NTU), Singapore. It integrates cryptographic primitives such as digital signatures, blind signatures, and homomorphic encryption into a full election lifecycle system.

> ⚠️ This system is intended for academic purposes and not for national-scale deployments.

---

## Project Objectives

- Implement cryptographic voting with provable privacy and auditability
- Prevent vote coercion and impersonation using blind signatures and 2FA
- Enable anonymous yet verifiable vote tallying with homomorphic encryption
- Ensure tamper resistance and full audit trails for administrators

---

## Security Pillars

| Pillar           | Implementation                                                                 |
|------------------|---------------------------------------------------------------------------------|
| **Confidentiality**   | Votes are encrypted using Paillier Homomorphic Encryption                  |
| **Authenticity**      | Digital Signatures + OTP 2FA + Session IP logging                         |
| **Anonymity**         | Blinded tokens unlink voter identity from vote                            |
| **Auditability**      | Zero-Knowledge Proofs (ZKP) for vote commitment verification               |
| **Tamper Resistance** | Admin actions logged with hash chaining + Tally locked post-election       |

---

## Tech Stack

| Layer        | Technology                                           |
|--------------|------------------------------------------------------|
| Frontend     | (Planned) Vue.js / React.js                         |
| Backend      | Flask (Python)                                      |
| Cryptography | PyCryptodome, PyOTP, phe (Paillier)                 |
| Database     | PostgreSQL                                          |
| Auth         | SHA-256, RSA / ECDSA + Blind Signatures             |
| 2FA          | PyOTP + QR Code                                     |
| Audit Report | ZKPs, CSV & PDF report generation                   |
| Testing      | Pytest + Coverage Suite                             |

---

## System Overview

### Voter Flow

1. `POST /register`  
   - Register with NTU email → receive verification link  
2. `GET /verify-email?token=...`  
   - Confirm email → receive TOTP QR  
3. `POST /login`  
   - Get nonce for signing  
4. `POST /login` with signed nonce  
   - Verify signature  
5. `POST /2fa-verify`  
   - Submit OTP  
6. `POST /claim-token`  
   - Receive blinded signed voting token  
7. `POST /cast_vote`  
   - Submit encrypted vote with signed token  

### 🛠️ Admin Flow

1. `POST /admin/start-election/<id>`  
2. `GET /admin/election-status/<id>`  
3. `POST /admin/end-election/<id>`  
4. `POST /admin/tally-election/<id>`  
   - Tallies votes with Paillier HE  
   - Generates ZKPs for verification  
5. `GET /admin/audit-report/<id>`  
   - View JSON result with proofs  
6. `GET /admin/download-report/<id>?format=csv/pdf`  
   - Download full report  
7. `GET /admin/verify-proof`  
   - Verifier portal (manual hash checks)

---

## Database Schema Summary

| Table                   | Description                                            |
|------------------------|--------------------------------------------------------|
| `voter`                | Voter credentials, verification status, public key     |
| `issued_tokens`        | Blinded tokens issued to verified voters               |
| `encrypted_votes`      | Paillier-encrypted votes + token hash                 |
| `election`             | Metadata for election lifecycle & control              |
| `admin_log`            | Tracks admin actions and audit events                  |
| `encrypted_candidate_votes` | Stores individual encrypted votes per candidate     |

---

## Testing & Coverage

```bash
pytest --cov=backend backend/tests/ -v
```

Fully tested with >90% coverage for:
- Voter registration, login, 2FA
- Token issuance, uniqueness constraint
- Vote encryption, token linking
- Election state changes
- Tallying correctness, aggregation edge cases
- ZKP generation + commitment validation
- Admin action hash chaining

---

## Audit Reports

Downloadable via:

```bash
GET /admin/download-report/<election_id>?format=csv
GET /admin/download-report/<election_id>?format=pdf
```

PDF includes:
- NTU logo
- Timestamp and election ID
- Candidate-wise vote tally
- ZKP salt, hash commitment
- Admin hash log trail

---

## Getting Started (Local Dev)

```bash
git clone https://github.com/yourusername/CryptoVote-FYP.git
cd CryptoVote-FYP/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

## License

This project is licensed under the **GNU Affero General Public License v3.0**.

You are free to use, modify, and distribute the software, but **you must disclose your source code** if:

- You modify the software and run it on a server, **and**
- Users interact with it over a network

**License Summary:**
- ✅ Commercial use allowed
- ✅ Derivatives allowed (must also be AGPL)
- ❌ Cannot use privately without sharing source
- ✅ Must preserve license and attribution

[Read Full License](https://www.gnu.org/licenses/agpl-3.0.html)

---

## Contact

**Alvin Aw Yong**  
Computer Engineering (NTU FYP)  
[LinkedIn](www.linkedin.com/in/alvin-aw-yong-3087591a6) | [Email](mailto:aavyong001@e.ntu.edu.sg)
