<div align="center">

# Prepzo

### Prepare · Practice · Perform

**AI-powered interview preparation platform** — company-specific question banks, timed mock interviews, ML answer scoring, and analytics.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![Vercel](https://img.shields.io/badge/Deployed_on-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://prepzo-ai.vercel.app)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

[Live Demo](https://prepzo-ai.vercel.app) · [Features](#features) · [Architecture](#architecture) · [API](#api-overview) · [Deploy](#deployment)

</div>

---

## Overview

Prepzo is a **full-stack AI interview prep SaaS** built for candidates targeting top tech and consulting companies. Practice with realistic timers, company-filtered questions, and instant ML feedback — all in a premium dark UI with zero framework bloat on the frontend.

| | |
|---|---|
| **Target users** | Job seekers preparing for FAANG, IT services, and product companies |
| **Core value** | Company-wise prep, timed interviews, AI scoring, progress analytics |
| **Production DB** | MongoDB Atlas only |
| **Deployment** | Vercel (static frontend + Python serverless API) |

---

## Features

### Interview experience
- **Company-wise preparation** — Amazon, Google, Microsoft, and 20+ employers
- **Mixed companies mode** — random cross-company practice
- **Professional timer system** — mandatory prep phase, difficulty-based answer limits, 30-minute session cap
- **No answer spoilers** — ideal answers only after submission

### AI & analytics
- **ML answer evaluation** — TF-IDF content match, communication, grammar, confidence scores
- **Score breakdown charts** — visual feedback after each answer
- **Dashboard & results** — streaks, progress, leaderboards, time analytics

### Platform
- **JWT authentication** — register, login, secure API access
- **Admin panel** — companies, questions, bulk upload, timer settings, users
- **MongoDB Atlas** — scalable, production-grade persistence

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, Vanilla JavaScript (no React/Tailwind CDN) |
| Backend | Flask 3, modular blueprints, REST JSON API |
| Database | MongoDB Atlas via PyMongo |
| ML | scikit-learn TF-IDF + heuristic scoring |
| Auth | JWT (PyJWT), bcrypt |
| Deploy | Vercel — `@vercel/python` + static frontend |

---

## Architecture

```mermaid
flowchart TB
    subgraph Client
        UI[frontend/ static UI]
    end
    subgraph Vercel
        WSGI[backend/wsgi.py]
        API[Flask API]
    end
    subgraph Data
        Atlas[(MongoDB Atlas)]
    end
    subgraph ML
        EV[ml/evaluator.py]
    end
    UI -->|/api/*| WSGI
    WSGI --> API
    API --> Atlas
    API --> EV
```

---

## Folder structure

```
prepzo/
├── frontend/          # Static UI (landing, auth, dashboard, interview, admin)
│   ├── css/
│   ├── js/
│   ├── admin/
│   └── assets/
├── backend/           # Flask API
│   ├── app.py         # Application factory
│   ├── wsgi.py        # Vercel entry point
│   ├── config.py
│   ├── extensions.py  # MongoDB connection
│   ├── routes/        # API blueprints
│   └── utils/
├── database/          # Seed scripts + question bank JSON
├── ml/                # Answer evaluator
├── requirements.txt
├── vercel.json
├── .env.example
└── README.md
```

---

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Service & MongoDB status |
| `POST` | `/api/auth/register` | Create account → `201` |
| `POST` | `/api/auth/login` | Sign in → `200` |
| `GET` | `/api/companies` | List companies |
| `GET` | `/api/questions` | Questions (`?company_id=`, `preview=true`) |
| `GET` | `/api/questions/mixed` | Random multi-company set |
| `POST` | `/api/evaluate` | ML answer scoring |
| `POST` | `/api/progress` | Save practice session |
| `GET` | `/api/progress/stats` | Dashboard statistics |

All responses are **JSON**. Errors return `{ "error": "..." }` with appropriate HTTP status codes.

---

## Installation

### Prerequisites
- Python 3.11+
- MongoDB Atlas cluster
- Git

### 1. Clone & install

```bash
git clone https://github.com/divyanallamolu/prepzo.ai.git
cd prepzo.ai
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
```

### 2. Environment

```bash
cp .env.example backend/.env
# Edit backend/.env with your Atlas URI and secrets
```

### 3. Seed database

```bash
cd database
python seed_data.py
python generate_question_bank.py
python seed_questions.py --force
```

### 4. Run locally

```bash
cd backend
python app.py
```

Open **http://127.0.0.1:5000** — API and frontend served together.

---

## Deployment

### Vercel

1. Import the GitHub repo in [Vercel](https://vercel.com).
2. **Root directory:** repository root (where `vercel.json` lives).
3. Add environment variables:

| Variable | Required |
|----------|----------|
| `MONGO_URI` | Yes — `mongodb+srv://.../prepzo?...` |
| `JWT_SECRET_KEY` | Yes |
| `FLASK_SECRET_KEY` | Yes |

4. Deploy. Verify:

```
https://your-app.vercel.app/api/health
```

### Atlas checklist
- Database user with read/write access
- Network access: allow `0.0.0.0/0` (or Vercel IPs)
- URI includes database name: `/prepzo`

---

## Environment variables

See [`.env.example`](.env.example) for the full template.

```env
MONGO_URI=mongodb+srv://USER:PASS@cluster.mongodb.net/prepzo?retryWrites=true&w=majority
JWT_SECRET_KEY=your-long-random-secret
FLASK_SECRET_KEY=your-flask-secret
```

---

## Screenshots

| Landing | Dashboard | Interview room |
|---------|-----------|----------------|
| Premium dark hero, company grid | Stats, company picker, mixed mode | Timers, AI evaluate, score bars |

_Add screenshots to `docs/screenshots/` and embed here for your portfolio._

---

## Future scope

- [ ] OAuth (Google / LinkedIn)
- [ ] Real-time interview coach (streaming hints)
- [ ] Resume-aware question generation
- [ ] Team / campus recruiter dashboards
- [ ] Mobile PWA install
- [ ] Cloud logo storage (S3 / Cloudinary)

---

## License

MIT © Prepzo

---

<div align="center">

**Built for serious interview preparation — portfolio-ready, production-deployed.**

[⭐ Star this repo](https://github.com/divyanallamolu/prepzo.ai) if Prepzo helps your prep journey.

</div>
