"""Performance analytics and motivational insights."""
from collections import defaultdict
from datetime import datetime, timezone

from bson import ObjectId

PASS_THRESHOLD = 60


def build_dashboard(db, user_id: str) -> dict:
    user = db.users.find_one({"_id": ObjectId(user_id)}) or {}
    progress = list(db.progress.find({"user_id": user_id}))

    total = len(progress)
    correct = sum(1 for p in progress if float(p.get("score", 0)) >= PASS_THRESHOLD)
    wrong = total - correct
    accuracy = round((correct / total) * 100, 1) if total else 0

    by_category = defaultdict(lambda: {"attempted": 0, "correct": 0, "total_score": 0.0})
    by_company = defaultdict(lambda: {"attempted": 0, "correct": 0})
    for p in progress:
        cat = p.get("category") or "General"
        co = p.get("company_name") or "Unknown"
        score = float(p.get("score", 0))
        by_category[cat]["attempted"] += 1
        by_category[cat]["total_score"] += score
        if score >= PASS_THRESHOLD:
            by_category[cat]["correct"] += 1
        by_company[co]["attempted"] += 1
        if score >= PASS_THRESHOLD:
            by_company[co]["correct"] += 1

    cat_perf = []
    for cat, v in by_category.items():
        acc = round((v["correct"] / v["attempted"]) * 100, 1) if v["attempted"] else 0
        cat_perf.append({
            "category": cat,
            "attempted": v["attempted"],
            "correct": v["correct"],
            "accuracy": acc,
            "avg_score": round(v["total_score"] / v["attempted"], 1) if v["attempted"] else 0,
        })
    cat_perf.sort(key=lambda x: x["accuracy"])

    weak = [c for c in cat_perf if c["attempted"] >= 2 and c["accuracy"] < 55][:5]
    strong = [c for c in reversed(cat_perf) if c["attempted"] >= 2 and c["accuracy"] >= 70][:5]

    company_perf = [
        {
            "company": k,
            "attempted": v["attempted"],
            "correct": v["correct"],
            "accuracy": round((v["correct"] / v["attempted"]) * 100, 1) if v["attempted"] else 0,
        }
        for k, v in by_company.items()
    ]
    company_perf.sort(key=lambda x: -x["attempted"])

    from services.streak_service import weekly_activity
    weekly = weekly_activity(db, user_id)

    today_count = db.progress.count_documents({
        "user_id": user_id,
        "completed_at": {"$gte": datetime.now(timezone.utc).date().isoformat()},
    })

    messages = _motivational_messages(
        user, total, correct, today_count, accuracy, weak, strong
    )

    return {
        "total_attempted": total,
        "correct": correct,
        "wrong": wrong,
        "accuracy": accuracy,
        "streak": user.get("streak", 0),
        "longest_streak": user.get("longest_streak", 0),
        "xp": user.get("xp", total * 10),
        "by_category": cat_perf,
        "by_company": company_perf[:10],
        "weak_topics": weak,
        "strong_topics": strong,
        "weekly_activity": weekly,
        "motivation": messages,
        "percentile_hint": min(95, 50 + accuracy // 2),
    }


def _motivational_messages(user, total, correct, today_count, accuracy, weak, strong) -> list:
    msgs = []
    streak = user.get("streak", 0)
    if today_count > 0:
        msgs.append(f"You solved {today_count} question{'s' if today_count != 1 else ''} today 🔥")
    if streak >= 3:
        msgs.append(f"Keep your {streak}-day streak alive — consistency wins interviews.")
    if strong:
        msgs.append(f"Strong in {strong[0]['category']} — accuracy {strong[0]['accuracy']}%.")
    if weak:
        msgs.append(f"Focus revision on {weak[0]['category']} to lift your overall score.")
    if accuracy >= 70 and total >= 5:
        msgs.append(f"You are ahead of {min(92, 55 + accuracy // 2)}% of learners on Prepzo.")
    if not msgs:
        msgs.append("Start your first practice session — every expert was once a beginner.")
    return msgs[:4]
