# Prepzo ML Module

## What it does

Scores interview answers using **simple NLP** (no neural networks, no spaCy).

| Score | How it's calculated |
|-------|---------------------|
| **Content (similarity)** | TF-IDF + cosine similarity between your answer and the ideal answer |
| **Communication** | Sentence length, word count, filler words (um, uh, like) |
| **Overall** | 60% content + 40% communication |

## Flow

```
Interview Room (frontend)
    → POST /api/evaluate  { user_answer, ideal_answer, category }
        → backend/routes/evaluate.py
            → ml/evaluator.py → evaluate_response()
    ← JSON scores + suggestions
```

## Files

- `ml/evaluator.py` — scoring logic (edit here to tune weights)
- `backend/routes/evaluate.py` — API endpoint (requires user login JWT)

## Local setup

```bash
cd backend
pip install -r requirements.txt
# scikit-learn is the only ML dependency
```

## Tuning

In `evaluator.py`:

- Change `0.6` / `0.4` in `overall` for content vs communication weight
- Edit `_generate_suggestions()` for custom feedback text

## Production (Vercel)

Uses the same `evaluator.py` via `api/index.py` serverless handler. No extra ML model downloads required.
