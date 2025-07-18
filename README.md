
# 🗳️ CryptoVote – Cryptographic Electronic Voting System (NTU FYP)

**CryptoVote** is a secure, privacy-preserving e-voting prototype developed as a Final Year Project (FYP) at Nanyang Technological University (NTU), Singapore. It integrates advanced cryptographic techniques—digital signatures, blind signatures, and homomorphic encryption—across the full election lifecycle.

> ⚠️ For educational and research use only. Not suitable for real-world governmental deployments.

---

## 🎯 Objectives

- ✅ Ensure **privacy** and **verifiability** using cryptographic constructs  
- ✅ Prevent vote manipulation, coercion, and impersonation  
- ✅ Support **end-to-end verifiability** with blind signatures and 2FA  
- ✅ Enable **anonymous** yet **auditable** homomorphic vote tallying  
- ✅ Provide traceable logs and proofs for **election integrity**

---

## 🔐 Core Security Pillars

| Pillar              | Implementation Highlights                                                       |
|---------------------|----------------------------------------------------------------------------------|
| **Confidentiality** | Paillier Homomorphic Encryption ensures votes stay secret                        |
| **Authenticity**    | Digital Signature (RSA/ECDSA) + OTP (2FA) + Voter Nonce                         |
| **Anonymity**       | Blinded Token issuance breaks voter–vote linkage                                |
| **Auditability**    | ZKPs for vote proof, CSV/PDF logs, and election trail                           |
| **Integrity**       | Database-stored timestamps, token reuse prevention, admin action logging        |

---

## 📦 Tech Stack

| Layer         | Technology                                                |
|---------------|-----------------------------------------------------------|
| Frontend      | *(Planned)* Vue.js or React.js                           |
| Backend       | Flask (Python)                                            |
| Cryptography  | `PyCryptodome`, `phe` (Paillier), `PyOTP`                 |
| Auth          | RSA / ECDSA Digital Signatures, Blind Signatures         |
| Database      | PostgreSQL + pgAdmin                                      |
| Reports       | PDFKit (wkhtmltopdf), CSV, Flask Templates                |

---

## 🧩 System Architecture

### 🧑‍💻 Voter Operation Flow

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

### 🛠️ Admin Operation Flow

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

---

## 🧮 Database Schema Summary

| Table               | Description                                     |
|---------------------|-------------------------------------------------|
| `voter`             | Stores voter registration & public key info     |
| `issued_tokens`     | Stores blind tokens & usage status              |
| `encrypted_votes`   | Stores per-candidate Paillier-encrypted votes   |
| `election`          | Metadata and state of elections                 |
| `admin_log`         | Logs admin actions with timestamps              |

---

## 🧪 Testing & Coverage

```bash
pytest --cov=backend backend/tests/ -v
```

Tests included:
- Voter registration and OTP flow
- Token issuance and verification
- Vote encryption and replay protection
- Election state transitions
- ZKP generation and tally checks

---

## 📄 Audit Reports

Download audit trail:
```
GET /admin/download-report/<election_id>?format=csv
GET /admin/download-report/<election_id>?format=pdf
```

PDF includes:
- Timestamp
- Candidate tallies
- Commitment hash and proof
- NTU Branding

---

## 🚀 Local Development Setup

```bash
git clone https://github.com/yourusername/CryptoVote-FYP.git
cd CryptoVote-FYP/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

## 📜 License

Licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.

- ✅ Free for academic & commercial use  
- ✅ Modifications allowed  
- ❌ Cannot run privately without disclosing source code  
- ✅ Must retain original license  

[Full License Terms →](https://www.gnu.org/licenses/agpl-3.0.html)

---

## 📬 Contact

**Alvin Aw Yong**  
Computer Engineering – NTU Singapore  
[LinkedIn](https://www.linkedin.com/in/alvin-aw-yong-3087591a6)  
[Email](mailto:aavyong001@e.ntu.edu.sg)
