"""
Prepzo ML — lightweight answer evaluation (TF-IDF + communication + grammar + confidence).
No spaCy — works on Vercel serverless.
"""
import re
from collections import Counter
from typing import Any

_STOP = frozenset(
    "a an the and or but in on at to for of is are was were be been being have has had do does did "
    "will would could should may might must can this that these those it its i you he she they we "
    "my your our their with from by as about".split()
)

FILLER = re.compile(r"\b(um|uh|like|you know|basically|actually|sort of|kind of)\b", re.I)


def _tokenize(text: str) -> list[str]:
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return [w for w in text.split() if len(w) > 2 and w not in _STOP]


def _keywords(text: str, n: int = 12) -> list[str]:
    words = _tokenize(text)
    return [x for x, _ in Counter(words).most_common(n)] if words else []


def similarity_score(user: str, ideal: str) -> float:
    """TF-IDF cosine similarity (content match)."""
    if not user.strip() or not ideal.strip():
        return 0.0
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        m = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform([user, ideal])
        return round(float(cosine_similarity(m[0:1], m[1:2])[0][0]) * 100, 1)
    except Exception:
        u, i = set(_tokenize(user)), set(_tokenize(ideal))
        return round(len(u & i) / len(i) * 100, 1) if i else 0.0


def communication_score(text: str) -> float:
    if not text.strip():
        return 0.0
    words = text.split()
    sents = max(1, len(re.split(r"[.!?]+", text)))
    avg = len(words) / sents
    score = 45.0
    if 8 <= avg <= 22:
        score += 28
    elif 5 <= avg <= 28:
        score += 15
    if len(words) >= 25:
        score += 12
    if len(words) >= 60:
        score += 10
    score -= min(25, len(FILLER.findall(text)) * 4)
    return round(min(100, max(0, score)), 1)


def grammar_score(text: str) -> float:
    """Simple grammar/clarity heuristics (no heavy NLP)."""
    if not text.strip():
        return 0.0
    score = 70.0
    words = text.split()
    # Sentence starts with capital
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if sentences:
        caps = sum(1 for s in sentences if s[0].isupper())
        score += (caps / len(sentences)) * 15
    # Repeated words
    lowered = [w.lower() for w in words]
    repeats = len(words) - len(set(lowered))
    score -= min(20, repeats * 2)
    # Very short answers
    if len(words) < 15:
        score -= 15
    # Double spaces / obvious typos
    if "  " in text:
        score -= 5
    if re.search(r"\bi\b", text):
        score += 5  # uses first person (often good in interviews)
    return round(min(100, max(0, score)), 1)


def confidence_score(text: str) -> float:
    """Hedge words lower confidence; decisive language raises it."""
    if not text.strip():
        return 0.0
    lower = text.lower()
    hedges = len(re.findall(
        r"\b(maybe|perhaps|might|could be|i think|i guess|not sure|probably)\b", lower
    ))
    strong = len(re.findall(
        r"\b(definitely|certainly|achieved|implemented|led|delivered|resulted|improved)\b", lower
    ))
    score = 55 + min(25, strong * 5) - min(30, hedges * 6)
    if len(text.split()) >= 40:
        score += 10
    return round(min(100, max(0, score)), 1)


def _suggestions(sim, comm, gram, conf, missing, category="") -> list[str]:
    out = []
    if sim < 40:
        out.append("Strengthen content: align with key terms from the ideal answer.")
    elif sim < 65:
        out.append("Good foundation — add metrics, examples, and specifics.")
    else:
        out.append("Strong content match. Practice delivering under time pressure.")
    if comm < 55:
        out.append("Use STAR structure and shorter, clearer sentences.")
    if gram < 60:
        out.append("Improve grammar: check capitalization and reduce repetition.")
    if conf < 55:
        out.append("Sound more confident — reduce hedging and state outcomes clearly.")
    if missing[:3]:
        out.append("Mention: " + ", ".join(missing[:3]) + ".")
    if category == "Behavioral":
        out.append("Include your personal impact and measurable results.")
    return out[:6]


def evaluate_response(
    user_answer: str,
    ideal_answer: str,
    question: str = "",
    category: str = "",
) -> dict[str, Any]:
    sim = similarity_score(user_answer, ideal_answer)
    comm = communication_score(user_answer)
    gram = grammar_score(user_answer)
    conf = confidence_score(user_answer)

    ik, uk = set(_keywords(ideal_answer)), set(_keywords(user_answer))
    matched, missing = list(ik & uk), list(ik - uk)[:10]

    # Weighted overall: content 45%, communication 25%, grammar 15%, confidence 15%
    overall = round(sim * 0.45 + comm * 0.25 + gram * 0.15 + conf * 0.15, 1)

    weak = []
    if sim < 50:
        weak.append("Content accuracy")
    if comm < 60:
        weak.append("Communication")
    if gram < 60:
        weak.append("Grammar & clarity")
    if conf < 55:
        weak.append("Confidence")
    if len(user_answer.split()) < 20:
        weak.append("Answer depth")

    return {
        "similarity_score": sim,
        "communication_score": comm,
        "grammar_score": gram,
        "confidence_score": conf,
        "overall_score": overall,
        "keywords_matched": matched[:15],
        "keywords_missing": missing,
        "suggestions": _suggestions(sim, comm, gram, conf, missing, category),
        "weak_areas": weak,
        "score_breakdown": {
            "content": sim,
            "communication": comm,
            "grammar": gram,
            "confidence": conf,
        },
        "feedback": (
            f"Overall: {overall}/100. Content {sim}%, Communication {comm}%, "
            f"Grammar {gram}%, Confidence {conf}%."
        ),
    }
