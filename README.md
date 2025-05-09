# 🗳️ CryptoVote – Cryptographic Electronic Voting System (NTU FYP)

**CryptoVote** is a cryptographic e-voting prototype developed as part of an undergraduate Final Year Project (FYP) at Nanyang Technological University (NTU), Singapore. It showcases key cryptographic principles like digital signatures, blind signatures, and homomorphic encryption applied to a simplified, privacy-preserving voting workflow.

> ⚠️ This project is **for educational purposes only** and does not guarantee full security or scalability.

---

## 🎯 Project Objectives

- Explore cryptographic techniques in voting systems
- Implement privacy-preserving voter authentication (digital signatures + 2FA)
- Allow encrypted vote casting using homomorphic encryption (Paillier)
- Ensure basic verifiability and auditability using cryptographic proofs

---

## 📦 Tech Stack

| Component       | Technologies                          |
|----------------|---------------------------------------|
| Frontend        | React.js / Vue.js                     |
| Backend         | Python (Flask or Django)              |
| Cryptography    | PyCryptodome, PyOTP, phe (Paillier)   |
| Database        | PostgreSQL / MySQL + SHA-256 hashing  |
| Email Services  | Flask-Mail / Django Email             |
| 2FA             | PyOTP, qrcode                         |
| Deployment      | Localhost / Docker / Cloud (Optional) |

---

## 🏗️ System Architecture

The system includes:

1. **Voter Interface** – Register, authenticate, cast vote
2. **Authentication Module** – Email domain check, digital signature, OTP-based 2FA
3. **Backend & DB** – Secure key generation, encrypted vote storage
4. **Audit Module** – Admin vote tally + basic cryptographic proof generation

---

## 🚀 Getting Started

### Backend Setup (Flask)
```bash
git clone https://github.com/yourusername/CryptoVote-FYP.git
cd CryptoVote-FYP/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

## 🔐 Authentication & Voting Flow (Testing with Postman)

### 🧾 Phase 1: Voter Registration
**POST** `/register`
```json
{
  "email": "aavyong001@e.ntu.edu.sg"
}
```
Expected: Returns `private_key` + verification token

### 🧾 Phase 2: Email Verification
**GET** `/register/verify-email?token=<token>`
Expected: Returns `totp_uri`
- Run `preview_qr.py` with the URI
- Scan with Google Authenticator

### 🧾 Phase 3: Login (Nonce-Based Digital Signature)
1. **POST** `/login` → returns `nonce`
2. Run `sign_nonce.py` with private key and nonce
3. **POST** `/login` with `signed_nonce`
Expected: Signature verified, login successful

### 🧾 Phase 4: 2FA Verification
**POST** `/2fa-verify`
```json
{
  "email": "aavyong001@e.ntu.edu.sg",
  "otp": "123456"
}
```
Expected: `vote_status = true`, 2FA success

### 🧾 Phase 5: Logout
**POST** `/logout`
```json
{
  "email": "aavyong001@e.ntu.edu.sg"
}
```
Expected: `logged_in = false`

---

## 📊 SQL to Monitor State (pgAdmin / psql)
```sql
SELECT id, email_hash, is_verified, logged_in, vote_status, has_votted,
       last_login_ip, last_login_at, last_2fa_at, created_at
FROM voter
ORDER BY id ASC;
```

---

For advanced cryptographic components like vote encryption and blind signing, see `/services/crypto_utils.py` and `/routes/vote.py` (to be implemented in next phases).
