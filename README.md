
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
| Backend         | Python (Flask)                        |
| Cryptography    | PyCryptodome, PyOTP, phe (Paillier)   |
| Database        | PostgreSQL / MySQL + SHA-256 hashing  |
| Email Services  | Flask-Mail                             |
| 2FA             | PyOTP, qrcode                         |
| Deployment      | Localhost / Docker / Cloud (Optional) |

### 🛠️ Tools & Libraries

| Purpose                | Tool/Library                      |
|------------------------|----------------------------------|
| Backend Framework      | Flask                            |
| Cryptography           | pycryptodome, ecdsa              |
| Database               | PostgreSQL                       |
| Hashing                | hashlib (SHA-256)                |
| Email Verification     | Flask-Mail                       |
| 2FA                    | PyOTP, qrcode, pyqrcode          |
| Token Generation       | itsdangerous or JWT              |

---

## 🏗️ System Architecture

The system includes:

1. **Voter Interface** – Register, authenticate, cast vote
2. **Authentication Module** – Email domain check, digital signature, OTP-based 2FA
3. **Backend & DB** – Secure key generation, encrypted vote storage
4. **Audit Module** – Admin vote tally + basic cryptographic proof generation

---

## 🔐 Authentication Module Design

### Authentication Module
The authentication module ensures legitimacy of voters and protects against impersonation:
- ✅ Verifies voter identity via NTU school email domain (`@ntu.edu.sg`)
- ✅ Employs **digital signatures** and **blind signatures** to issue credentials securely
- ✅ Implements **2FA** using TOTP (e.g., Google Authenticator)
- ✅ (Planned) Support for **ZKP** proofs in future phases

### 🔧  Development Plan

#### Voter Registration Setup
**Objective:** Enable only valid users (e.g., NTU students) to register securely.

**Tasks:**
- Setup PostgreSQL/MySQL database for storing voter metadata
- Create Flask/Django API endpoints:
  - `/register` – Accepts school email, sends verification token
  - `/verify-email` – Confirms registration via token link
- Validate NTU email domain (e.g., ends with @ntu.edu.sg)
- Generate asymmetric key pair (RSA/ECDSA) per voter
- Store public key and hashed email in DB (SHA-256)
- Create test suite to verify voter registration flow

**Backend Flow:**
- User registers with email
- Backend checks domain + generates token
- On confirmation → public/private keypair created
- Public key stored; private key kept client-side only

#### 2FA and Authentication
**Objective:** Ensure tamper-proof login and secure session for vote casting

**Tasks:**
- Implement TOTP (Time-Based OTP) with PyOTP
- Add `/login`, `/2fa-verify`, `/logged_in` endpoints
- Use challenge-response digital signature login:
  - Server sends nonce → Voter signs → Server verifies
- Log login IP + timestamp (optional)

**Backend Flow:**
- Voter enters email
- Server sends nonce
- Voter signs nonce with private key → sends back
- Server verifies → prompts OTP
- TOTP verified → session allowed

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

### Run Test Suite
```bash
pytest --cov=backend backend/tests/ -v
```
> 💡 Tip: Use `pytest-html` to generate test reports for better visualization.

---

## 🧪 Authentication & Voting Flow (Testing with Postman)

### Voter Registration
**POST** `/register`
```json
{
  "email": "aavyong001@e.ntu.edu.sg"
}
```
Expected: Returns `private_key` + verification token

### Email Verification
**GET** `/register/verify-email?token=<token>`
Expected: Returns `totp_uri`
- Run `preview_qr.py` with the URI
- Scan using Google Authenticator

### Login (Nonce-Based Digital Signature)
1. **POST** `/login` → returns `nonce`
2. Run `sign_nonce.py` with private key and nonce
3. **POST** `/login` with `signed_nonce`
Expected: Signature verified, login successful

### 2FA Verification
**POST** `/2fa-verify`
```json
{
  "email": "aavyong001@e.ntu.edu.sg",
  "otp": "123456"
}
```
Expected: `vote_status = true`, 2FA success

### Logout
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

For advanced cryptographic components like vote encryption and blind signing, see `/services/crypto_utils.py` and `/routes/vote.py` (to be implemented in next phases).
