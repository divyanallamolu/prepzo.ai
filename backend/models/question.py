"""Question document serializer."""


def serialize_question(doc: dict, include_answer: bool = True) -> dict:
    text = doc.get("question_text") or doc.get("question", "")
    q = {
        "id": str(doc["_id"]),
        "company_id": doc.get("company_id", ""),
        "company_name": doc.get("company_name", ""),
        "title": doc.get("title", text[:80] if text else ""),
        "difficulty": doc.get("difficulty", "Medium"),
        "category": doc.get("category", "Technical"),
        "question_text": text,
        "question": text,
        "tips": doc.get("tips", []),
        "tags": doc.get("tags", []),
        "frequency": doc.get("frequency", "Medium"),
        "estimated_time": doc.get("estimated_time", 60),
        "year_asked": doc.get("year_asked", ""),
        "key_points": doc.get("key_points", []),
    }
    if include_answer:
        ans = doc.get("expected_answer") or doc.get("answer", "")
        q["expected_answer"] = ans
        q["answer"] = ans
        q["explanation"] = doc.get("explanation", ans)
    return q
