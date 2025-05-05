# 🗳️ CryptoVote – Cryptographic Electronic Voting System (NTU FYP)

**CryptoVote** is a cryptographic e-voting prototype developed as part of an undergraduate Final Year Project (FYP) at Nanyang Technological University (NTU), Singapore. It showcases key cryptographic principles like digital signatures, blind signatures, and homomorphic encryption applied to a simplified, privacy-preserving voting workflow.

---

## 🎯 Project Objectives

- Explore cryptographic techniques in voting systems
- Implement privacy-preserving voter authentication (digital signatures + 2FA)
- Allow encrypted vote casting using homomorphic encryption (Paillier)
- Ensure basic verifiability and auditability using cryptographic proofs

> ⚠️ This project is **for educational purposes only** and does not guarantee full security or scalability.

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
