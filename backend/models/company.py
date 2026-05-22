"""Company document serializer."""


def serialize_company(doc: dict, include_meta: bool = True) -> dict:
    out = {
        "id": str(doc["_id"]),
        "name": doc.get("name", ""),
        "slug": doc.get("slug", ""),
        "logo": doc.get("logo", ""),
        "description": doc.get("description", ""),
        "difficulty": doc.get("difficulty", "Medium"),
        "category": doc.get("category", "Product"),
        "trending": bool(doc.get("trending", False)),
        "tags": doc.get("tags", []),
        "interview_count": doc.get("interview_count", 0),
        "question_count": doc.get("question_count", 0),
        "estimated_salary": doc.get("estimated_salary", ""),
        "preparation_time": doc.get("preparation_time", ""),
        "hiring_status": doc.get("hiring_status", ""),
        "popularity_score": doc.get("popularity_score", 0),
    }
    return out
