"""Revision lists — wrong, bookmarked, missed topics."""
from bson import ObjectId

PASS_THRESHOLD = 60


def get_revision_pack(db, user_id: str) -> dict:
    wrong = list(db.progress.find({
        "user_id": user_id,
        "score": {"$lt": PASS_THRESHOLD},
    }).sort("completed_at", -1).limit(30))

    bookmarks = list(db.bookmarks.find({"user_id": user_id}).sort("created_at", -1).limit(30))

    missed_pipeline = [
        {"$match": {"user_id": user_id, "score": {"$lt": PASS_THRESHOLD}}},
        {"$group": {"_id": "$question_id", "count": {"$sum": 1}, "last_score": {"$last": "$score"}}},
        {"$match": {"count": {"$gte": 2}}},
        {"$sort": {"count": -1}},
        {"$limit": 15},
    ]
    frequent = list(db.progress.aggregate(missed_pipeline))

    recent = list(db.progress.find({"user_id": user_id}).sort("completed_at", -1).limit(15))

    def enrich_progress(items):
        out = []
        for p in items:
            qid = p.get("question_id")
            q = db.questions.find_one({"_id": ObjectId(qid)}) if ObjectId.is_valid(str(qid)) else None
            out.append({
                "progress_id": str(p.get("_id", "")),
                "question_id": qid,
                "company_name": p.get("company_name", ""),
                "category": p.get("category", ""),
                "difficulty": p.get("difficulty", ""),
                "score": p.get("score", 0),
                "question_text": (q or {}).get("question_text", p.get("user_answer", "")[:120]),
                "title": (q or {}).get("title", ""),
                "completed_at": p.get("completed_at", ""),
            })
        return out

    def enrich_bookmarks(items):
        out = []
        for b in items:
            qid = b.get("question_id")
            q = db.questions.find_one({"_id": ObjectId(qid)}) if ObjectId.is_valid(str(qid)) else None
            out.append({
                "question_id": qid,
                "company_name": b.get("company_name", ""),
                "question_text": b.get("question_text") or (q or {}).get("question_text", ""),
                "title": (q or {}).get("title", ""),
                "category": (q or {}).get("category", ""),
                "difficulty": (q or {}).get("difficulty", ""),
            })
        return out

    frequent_out = []
    for f in frequent:
        qid = f["_id"]
        q = db.questions.find_one({"_id": ObjectId(qid)}) if ObjectId.is_valid(str(qid)) else None
        if q:
            frequent_out.append({
                "question_id": qid,
                "miss_count": f["count"],
                "last_score": f.get("last_score", 0),
                "title": q.get("title", ""),
                "category": q.get("category", ""),
                "company_name": q.get("company_name", ""),
            })

    return {
        "wrong_questions": enrich_progress(wrong),
        "bookmarked": enrich_bookmarks(bookmarks),
        "frequently_missed": frequent_out,
        "recently_practiced": enrich_progress(recent),
    }
