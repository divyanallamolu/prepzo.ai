"""
Generate 25+ interview questions per company across all categories.
Run: python generate_questions.py
Output: database/data/questions.json
"""
import json
import os
from itertools import cycle

from companies_config import COMPANIES

CATEGORIES = [
    "DSA",
    "System Design",
    "HR",
    "OOPs",
    "DBMS",
    "OS",
    "Networking",
    "Behavioral",
    "SQL",
    "Coding Rounds",
]

TEMPLATES = {
    "DSA": [
        ("Two Sum Variant at {co}", "Easy", "Given an array and target, return indices using a hash map in O(n).", "Use a hash map to store complements; one pass O(n) time, O(n) space.", ["Use hash map", "Clarify duplicates", "State complexity"]),
        ("LRU Cache for {co} Services", "Hard", "Design a Least Recently Used cache with O(1) get and put.", "Hash map + doubly linked list; explain eviction policy and thread safety if asked.", ["O(1) operations", "Capacity bounds", "Concurrency"]),
        ("Binary Tree Level Order", "Medium", "Return level-order traversal of a binary tree.", "BFS with queue; track level sizes for zigzag variants.", ["BFS", "Null checks", "Space O(n)"]),
        ("Merge Intervals Pipeline", "Medium", "Merge overlapping intervals from scheduling data.", "Sort by start, merge if overlap; discuss edge cases for open intervals.", ["Sort first", "Edge cases", "Complexity"]),
        ("Graph Shortest Path", "Hard", "Find shortest path in weighted graph with non-negative edges.", "Dijkstra with min-heap; mention Bellman-Ford if negative edges allowed.", ["Heap", "Relaxation", "Complexity"]),
    ],
    "System Design": [
        ("Design {co} News Feed", "Hard", "Design a scalable home feed for millions of daily active users.", "Fan-out on write vs read; caching; ranking layer; CDN for media.", ["Sharding", "Cache", "Ranking"]),
        ("Rate Limiter API", "Medium", "Design a distributed rate limiting service.", "Token bucket or sliding window in Redis; per-user keys; graceful 429 responses.", ["Redis", "Consistency", "Burst"]),
        ("Notification System", "Medium", "Design push/email notification delivery at scale.", "Queue workers, idempotency keys, retry with DLQ, user preference store.", ["Queues", "Idempotency", "Retries"]),
        ("Search Autocomplete", "Hard", "Design typeahead search for {co} products.", "Trie + popular queries cache; debounce client; ES cluster for fuzzy match.", ["Trie", "Caching", "Ranking"]),
    ],
    "HR": [
        ("Why {co}?", "Easy", "Why do you want to join {co} specifically?", "Connect mission, product impact, and your skills; mention recent news or values.", ["Research company", "Be specific", "Authenticity"]),
        ("Tell Me About Yourself", "Easy", "Walk me through your background in 2 minutes.", "Present → past → future; align with role; end with why this team.", ["Structure", "Relevance", "Concise"]),
        ("Strengths & Weaknesses", "Medium", "What are your strengths and areas for growth?", "Strength with example; weakness with improvement plan; avoid clichés.", ["STAR examples", "Growth mindset", "Honesty"]),
    ],
    "OOPs": [
        ("SOLID at {co}", "Medium", "Explain SOLID principles with examples from your projects.", "SRP, OCP, LSP, ISP, DIP — one sentence each with code-level example.", ["Real examples", "Trade-offs", "Design patterns"]),
        ("Inheritance vs Composition", "Medium", "When would you favor composition over inheritance?", "Composition for flexibility; inheritance for true is-a; discuss fragile base class.", ["UML optional", "Examples", "Maintainability"]),
    ],
    "DBMS": [
        ("Indexing Strategy", "Medium", "How do B-tree indexes speed up queries? When do they hurt?", "Faster reads, slower writes; composite index order matters; covering indexes.", ["Selectivity", "Explain plan", "Trade-offs"]),
        ("ACID vs BASE", "Medium", "Compare ACID transactions with eventual consistency (BASE).", "Banking needs ACID; social feeds may use eventual consistency with conflict resolution.", ["Use cases", "CAP theorem", "Examples"]),
        ("Normalization", "Easy", "Explain 1NF, 2NF, 3NF with a sample schema.", "Remove repeating groups, partial deps, transitive deps; denormalize for read perf when needed.", ["Examples", "Denormalization", "Anomalies"]),
    ],
    "OS": [
        ("Process vs Thread", "Easy", "Difference between process and thread? When use each?", "Processes isolated; threads share memory; thread cheaper; mention context switch cost.", ["Memory model", "IPC", "Examples"]),
        ("Deadlock Prevention", "Hard", "What is deadlock and how can you prevent it?", "Mutual exclusion, hold & wait, no preemption, circular wait; ordering resources, timeouts.", ["Four conditions", "Banker's algo", "Practical tips"]),
        ("Virtual Memory", "Medium", "Explain paging and virtual memory.", "MMU maps virtual to physical; page faults; TLB; working set.", ["Page tables", "Thrashing", "Locality"]),
    ],
    "Networking": [
        ("HTTP vs HTTPS", "Easy", "How does HTTPS secure web traffic?", "TLS handshake, certificates, symmetric encryption after key exchange.", ["TLS", "Certs", "MITM"]),
        ("TCP vs UDP", "Medium", "When choose TCP over UDP for {co} services?", "TCP reliable ordered; UDP for real-time/low latency; QUIC blends features.", ["Use cases", "Head-of-line", "Latency"]),
        ("DNS Resolution", "Medium", "What happens when you type a URL and press Enter?", "DNS lookup, TCP connect, TLS, HTTP request, render; mention caching layers.", ["DNS", "CDN", "Caching"]),
    ],
    "Behavioral": [
        ("Conflict with Teammate", "Medium", "Describe a conflict and how you resolved it.", "STAR format; focus on empathy, data, and outcome; avoid blaming.", ["STAR", "Outcome", "Learning"]),
        ("Failed Project", "Medium", "Tell me about a project that failed and what you learned.", "Own mistakes; metrics before/after; process improvements adopted.", ["Accountability", "Metrics", "Growth"]),
        ("Leadership Example", "Hard", "When did you lead without formal authority?", "Influence through clarity, documentation, and shipping; quantify impact.", ["Influence", "Impact", "Collaboration"]),
    ],
    "SQL": [
        ("Second Highest Salary", "Easy", "Write SQL to find second highest salary per department.", "DENSE_RANK or subquery with MAX; handle ties with LIMIT OFFSET carefully.", ["Window functions", "Ties", "Edge cases"]),
        ("JOIN Types", "Medium", "Explain INNER, LEFT, RIGHT, FULL joins with use cases.", "Diagram rows matched/unmatched; anti-join patterns for missing data.", ["Venn diagram", "Performance", "Indexes"]),
        ("Query Optimization", "Hard", "How would you optimize a slow analytics query?", "EXPLAIN plan, indexes, partition, materialized views, avoid SELECT *.", ["EXPLAIN", "Indexes", "Denormalize"]),
    ],
    "Coding Rounds": [
        ("String Permutations", "Medium", "Print all permutations of a string without duplicates.", "Backtracking with used array or swap method; discuss time O(n*n!).", ["Backtracking", "Duplicates", "Complexity"]),
        ("Valid Parentheses", "Easy", "Check if bracket string is valid.", "Stack; push open, pop on close; empty stack at end.", ["Stack", "Edge cases", "O(n)"]),
        ("Max Subarray Sum", "Medium", "Find maximum sum contiguous subarray (Kadane).", "Track current and global max; discuss all-negative array.", ["Kadane", "DP view", "O(n)"]),
    ],
}


def build_questions():
    out = []
    diff_cycle = cycle(["Easy", "Medium", "Hard"])
    for company in COMPANIES:
        co = company["name"]
        per_cat = max(2, 25 // len(CATEGORIES))
        count = 0
        for cat in CATEGORIES:
            templates = TEMPLATES.get(cat, TEMPLATES["DSA"])
            for i, (title_t, diff, qtext, answer, tips) in enumerate(templates):
                if count >= 25:
                    break
                title = title_t.format(co=co)
                difficulty = diff if diff else next(diff_cycle)
                out.append({
                    "company_name": co,
                    "title": title,
                    "difficulty": difficulty,
                    "category": cat,
                    "question_text": qtext,
                    "expected_answer": answer,
                    "answer": answer,
                    "explanation": answer,
                    "question": qtext,
                    "tips": tips,
                    "tags": [cat, co, difficulty],
                    "frequency": ["High", "Medium", "Low"][count % 3],
                    "estimated_time": 45 if difficulty == "Easy" else (90 if difficulty == "Medium" else 120),
                    "year_asked": str(2023 + (count % 3)),
                    "key_points": tips,
                })
                count += 1
            if count >= 25:
                break
        while count < 25:
            cat = CATEGORIES[count % len(CATEGORIES)]
            tpl = TEMPLATES[cat][0]
            title, diff, qtext, answer, tips = tpl
            out.append({
                "company_name": co,
                "title": title.format(co=co),
                "difficulty": next(diff_cycle),
                "category": cat,
                "question_text": qtext,
                "expected_answer": answer,
                "answer": answer,
                "explanation": answer,
                "question": qtext,
                "tips": tips,
                "tags": [cat, co],
                "frequency": "Medium",
                "estimated_time": 60,
                "year_asked": "2024",
                "key_points": tips,
            })
            count += 1
    return out


def main():
    questions = build_questions()
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "questions.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"questions": questions, "total": len(questions)}, f, indent=2)
    print(f"Wrote {len(questions)} questions to {path}")


if __name__ == "__main__":
    main()
