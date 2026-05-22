# Database

MongoDB Atlas is the **only** data store for Prepzo (no in-memory fallback).

## Seed scripts (run locally with `MONGO_URI` set)

```bash
# From project root
cp .env.example backend/.env   # or export MONGO_URI

cd database
python seed_data.py              # admin user + companies
python generate_question_bank.py # builds data/interview_questions.json
python seed_questions.py --force # loads 500+ questions
```

## Atlas URI format

```
mongodb+srv://USER:PASS@cluster.mongodb.net/prepzo?retryWrites=true&w=majority
```

Include the database name `/prepzo` in the URI.

## Collections

| Collection | Purpose |
|------------|---------|
| `users` | Auth, roles, streaks |
| `companies` | Interview companies |
| `questions` | Question bank |
| `progress` | Practice history |
| `timer_settings` | Admin timer config |
