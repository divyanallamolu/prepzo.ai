"""Practice streak tracking."""
from datetime import datetime, timedelta, timezone

from bson import ObjectId


def update_streak(db, user_id: str) -> dict:
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return {"streak": 0, "longest_streak": 0}

    today = datetime.now(timezone.utc).date().isoformat()
    last = user.get("last_practice")
    streak = int(user.get("streak", 0))
    longest = int(user.get("longest_streak", 0))

    if last == today:
        return {"streak": streak, "longest_streak": longest, "updated": False}

    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    if last == yesterday:
        streak += 1
    else:
        streak = 1

    longest = max(longest, streak)
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"streak": streak, "longest_streak": longest, "last_practice": today}},
    )
    return {"streak": streak, "longest_streak": longest, "updated": True}


def weekly_activity(db, user_id: str) -> list:
    """Last 7 days practice counts."""
    days = []
    for i in range(6, -1, -1):
        d = (datetime.now(timezone.utc).date() - timedelta(days=i)).isoformat()
        start = f"{d}T00:00:00"
        end = f"{d}T23:59:59"
        count = db.progress.count_documents({
            "user_id": user_id,
            "completed_at": {"$gte": start, "$lte": end},
        })
        days.append({"date": d, "count": count})
    return days
