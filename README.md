# 🛡️ CyberSec Dashboard — Phishing Awareness & Training Platform

A complete role-based cybersecurity dashboard system with two separate interfaces:
an **Admin Dashboard** for running phishing awareness campaigns and a **User Dashboard**
for training, simulations, and quizzes.

## ✨ Features

### Admin Dashboard
- **Overview** — stat cards, awareness trend, risk distribution, simulation stats, monthly activity, recent activity timeline
- **User Management** — add/edit/delete users, assign roles, CSV import, awareness score & risk level tracking
- **Campaign Management** — create/schedule/activate phishing simulations with 4 scenarios
- **Email Templates** — create/edit/preview templates with suspicious indicators & awareness explanations
- **Response Monitoring** — real-time tracking (opened, clicked, reported, page visited, quiz completed)
- **Analytics** — department-wise comparison, risk classification, phishing detection rate, leaderboard
- **Reports** — PDF + CSV export, recommendations, risk analysis

### User Dashboard
- **Home** — awareness score ring, risk level, pending simulations, notifications
- **Simulations** — simulated phishing mailbox where users analyze emails & report phishing
- **Training** — 6 awareness lessons (phishing, URL detection, social engineering, passwords, MFA) with per-lesson completion tracking
- **Quiz** — scenario-based multiple choice assessment
- **Results** — performance report, mistake analysis, recommendations
- **Profile** — update name/department/password
- **Certification** — a certificate unlocks on the dashboard once the user completes all:
  - ✅ All active phishing simulations
  - ✅ All training modules (marked complete)
  - ✅ Quiz with a passing score (≥ 80%)
  - ✅ Awareness score ≥ 80%
  - A locked card shows live progress; once unlocked, a **Download Certificate** button generates a professional PDF (jsPDF) with the platform logo, user name, title, completion date, unique certificate ID, signature placeholder, and official seal.

## 🚀 Quick Start

### 1. Set up the backend (Python 3.8+)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
pip install -r requirements.txt
```

### 2. Seed demo data

```bash
python seed.py
```

### 3. Run the server

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

## 🔑 Demo Accounts

| Role  | Email                | Password  |
|-------|----------------------|-----------|
| Admin | `admin@cybersec.com` | `admin123`|
| User  | `alice@example.com`  | `user123` |

## 🧱 Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js
- **Backend**: Python Flask
- **Database**: SQLite (MySQL-compatible schema)
- **Auth**: JWT (stdlib-only implementation) with role-based access control

## 📁 Project Structure

```
Major Project-2/
├── backend/
│   ├── app.py            # Flask app + all REST endpoints
│   ├── models.py         # Database schema (6+ tables)
│   ├── auth.py           # JWT auth & RBAC
│   ├── config.py         # App config
│   ├── seed.py           # Demo data generator
│   └── requirements.txt
├── frontend/
│   ├── login.html        # Role-based login
│   ├── admin/            # Admin Dashboard (10 pages)
│   └── user/             # User Dashboard (7 pages)
└── docs/
    ├── DESIGN.md         # Architecture, ER diagram, wireframes
    └── README.md
```

See **[docs/DESIGN.md](docs/DESIGN.md)** for the Mermaid architecture diagram, database ER diagram, and dashboard wireframes.

## 🔒 Security Notes

- This is a **training simulation** — no real passwords or sensitive data are collected.
- Only click behavior, awareness responses, and quiz answers are recorded.
- In production, replace the SHA-256 demo hashing with a strong KDF (e.g., bcrypt/argon2) and use HTTPS.
