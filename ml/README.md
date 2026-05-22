# ML — Answer evaluation

Lightweight scoring in `evaluator.py` (no spaCy, Vercel-friendly):

- **Content** — TF-IDF similarity vs ideal answer
- **Communication** — clarity and structure heuristics
- **Grammar** — basic grammar signals
- **Confidence** — hedge vs decisive language

Invoked by `POST /api/evaluate` from the interview room.
