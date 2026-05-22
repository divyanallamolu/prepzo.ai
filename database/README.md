# Prepzo Database Seeding

## Question bank (500 questions — 25 per company)

| File | Purpose |
|------|---------|
| `companies_config.py` | 20 company definitions |
| `generate_question_bank.py` | Builds `data/interview_questions.json` |
| `data/interview_questions.json` | Structured question data (committed to repo) |
| `seed_questions.py` | Inserts questions into MongoDB |

### Companies included

Google, Amazon, Microsoft, Meta, Netflix, Uber, Adobe, PayPal, Flipkart, Zoho, IBM, Accenture, Deloitte, Capgemini, TCS, Infosys, Wipro, Cognizant, Tech Mahindra, HCL

### Categories

HR, Technical, Behavioral, DSA, System Design, Communication

## Quick start

```bash
cd database

# 1. Generate JSON (optional if file already exists)
python generate_question_bank.py

# 2. Seed MongoDB (requires MongoDB running)
python seed_data.py          # admin + companies
python seed_questions.py     # all questions (skips duplicates)

# Fresh reload
python seed_questions.py --reset
```

## Flags

- `--reset` — delete all questions, re-insert from JSON
- `--force` — run even when questions already exist (still skips duplicates)

## Without MongoDB

Flask falls back to **in-memory** DB and auto-loads companies + questions from JSON on startup via `backend/utils/dev_seed.py`.
