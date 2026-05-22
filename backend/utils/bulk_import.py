import csv
import io
import json
from typing import Any


VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}
VALID_CATEGORIES = {"HR", "Technical", "Behavioral", "DSA", "System Design", "Communication"}


def normalize_difficulty(value: str) -> str:
    d = (value or "Medium").strip().title()
    return d if d in VALID_DIFFICULTIES else "Medium"


def normalize_category(value: str) -> str:
    raw = (value or "Technical").strip()
    # Preserve multi-word categories
    mapping = {
        "dsa": "DSA",
        "system design": "System Design",
        "communication": "Communication",
        "hr": "HR",
        "technical": "Technical",
        "behavioral": "Behavioral",
    }
    key = raw.lower()
    if key in mapping:
        return mapping[key]
    titled = raw.title()
    return titled if titled in VALID_CATEGORIES else "Technical"


def parse_csv_text(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV file is empty or missing headers")

    fields = {f.lower().strip(): f for f in reader.fieldnames}

    def col(name):
        return fields.get(name)

    required = ["company_name", "question", "answer"]
    for key in required:
        if key not in fields:
            raise ValueError(f"CSV missing required column: {key}")

    rows = []
    for i, row in enumerate(reader, start=2):
        item = {
            "company_name": (row.get(col("company_name")) or "").strip(),
            "question": (row.get(col("question")) or "").strip(),
            "answer": (row.get(col("answer")) or "").strip(),
            "explanation": (row.get(col("explanation")) or "").strip() if col("explanation") else "",
            "difficulty": normalize_difficulty(row.get(col("difficulty")) or "") if col("difficulty") else "",
            "category": normalize_category(row.get(col("category")) or "") if col("category") else "",
            "year_asked": (row.get(col("year_asked")) or "").strip() if col("year_asked") else "",
            "tags": [],
        }
        if not item["company_name"] or not item["question"] or not item["answer"]:
            continue
        if not item["explanation"]:
            item["explanation"] = item["answer"]
        rows.append(item)
    return rows


def parse_json_payload(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and "questions" in data:
        items = data["questions"]
    else:
        raise ValueError("JSON must be an array or { questions: [...] }")

    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        company = (item.get("company_name") or item.get("company") or "").strip()
        question = (item.get("question") or "").strip()
        answer = (item.get("answer") or "").strip()
        if not company or not question or not answer:
            continue
        explanation = (item.get("explanation") or "").strip() or answer
        rows.append({
            "company_name": company,
            "question": question,
            "answer": answer,
            "explanation": explanation,
            "difficulty": normalize_difficulty(item.get("difficulty", "")),
            "category": normalize_category(item.get("category", "")),
            "year_asked": (item.get("year_asked") or "").strip(),
            "tags": item.get("tags") or [],
        })
    return rows
