"""
Builds the full interview question bank (20+ per company).
Run: python generate_question_bank.py
Output: database/data/interview_questions.json
"""

import json
import os
from companies_config import COMPANIES

VALID_CATEGORIES = {"HR", "Technical", "Behavioral", "DSA", "System Design", "Communication"}
VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}


def item(company, question, answer, explanation, difficulty, category, year="2024", tags=None):
    return {
        "company_name": company,
        "question": question.strip(),
        "answer": answer.strip(),
        "explanation": explanation.strip(),
        "difficulty": difficulty if difficulty in VALID_DIFFICULTIES else "Medium",
        "category": category if category in VALID_CATEGORIES else "Technical",
        "year_asked": year,
        "tags": tags or [],
        "tips": [],
        "key_points": [],
    }


# ─── Shared modern question templates (customized per company) ───
def shared_pool(company):
    c = company
    return [
        item(c, f"Why do you want to join {c}?", 
             f"I am excited about {c}'s impact, engineering culture, and the chance to work on large-scale problems aligned with my skills. I have followed {c}'s recent product launches and want to contribute to customer-focused innovation.",
             "HR screens for motivation, role fit, and genuine research about the company.",
             "Easy", "HR", "2024", ["motivation", "culture"]),
        item(c, "Tell me about yourself.",
             "Give a 90-second pitch: current role, relevant achievements with metrics, why this domain excites you, and why this company/role is the natural next step.",
             "Structure: Present → Past → Future. Keep it concise and relevant to the job description.",
             "Easy", "HR", "2024", ["introduction"]),
        item(c, "Describe a time you failed and what you learned.",
             "Use STAR: explain the project failure without blaming others, your accountability, changes you made (process, testing, communication), and a later success using those lessons.",
             "Interviewers want ownership, reflection, and growth mindset.",
             "Medium", "Behavioral", "2024", ["failure", "STAR"]),
        item(c, "How do you handle tight deadlines with competing priorities?",
             "Clarify goals with stakeholders, break work into milestones, communicate risks early, automate repetitive tasks, and deliver an MVP while documenting tradeoffs.",
             "Tests prioritization and communication under pressure.",
             "Medium", "Behavioral", "2025", ["prioritization"]),
        item(c, "Explain time and space complexity of your recent project.",
             "Pick a real module: describe input size n, dominant operations (loops, hash lookups), Big-O notation, and optimizations applied (caching, indexing, batching).",
             "Shows you analyze production code, not only puzzles.",
             "Medium", "Technical", "2024", ["complexity"]),
        item(c, "Two Sum: return indices of two numbers that add to target.",
             "Use a hash map: for each value x, check if target-x exists; store value→index. Time O(n), space O(n). Mention handling duplicates and no-solution case.",
             "Classic warm-up DSA question still common in 2024–2025 screens.",
             "Easy", "DSA", "2024", ["arrays", "hash map"]),
        item(c, "Reverse a linked list iteratively and recursively.",
             "Iterative: three pointers prev/current/next, flip links. Recursive: reverse rest then point next to current. Both O(n) time, O(1)/O(n) space.",
             "Fundamental pointer manipulation test.",
             "Medium", "DSA", "2024", ["linked list"]),
        item(c, "Find the longest substring without repeating characters.",
             "Sliding window with hash set of chars in window; shrink left when duplicate. Time O(n), space O(min(n, charset)).",
             "Very common sliding-window pattern.",
             "Medium", "DSA", "2024", ["sliding window", "strings"]),
        item(c, "Design a rate limiter for an API.",
             "Options: token bucket or sliding window counter in Redis per user/IP; return 429 with Retry-After; discuss distributed consistency and burst traffic.",
             "System design + practical backend knowledge.",
             "Hard", "System Design", "2025", ["rate limiting", "API"]),
        item(c, "How would you design a notification system at scale?",
             "Producer → queue (Kafka/SQS) → workers per channel (email/push/SMS), idempotency keys, retry DLQ, user preference store, and delivery analytics.",
             "Tests async architecture and reliability thinking.",
             "Hard", "System Design", "2024", ["notifications", "queues"]),
        item(c, "Explain CAP theorem with a real example.",
             "In distributed stores you trade Consistency vs Availability during partitions; give example (bank balance vs social feed likes) and which choice fits the product.",
             "Expected in distributed systems discussions.",
             "Medium", "System Design", "2024", ["CAP", "distributed"]),
        item(c, "What is the difference between REST and GraphQL?",
             "REST: resource URLs, multiple round trips. GraphQL: single endpoint, client-specified fields, complexity limits needed. Choose based on client diversity and caching needs.",
             "API design literacy for full-stack roles.",
             "Easy", "Technical", "2024", ["API", "REST"]),
        item(c, "How do you ensure code quality in a fast-moving team?",
             "CI pipelines, unit/integration tests, linting, code reviews, feature flags, observability, and clear definition of done.",
             "Communication + engineering practices question.",
             "Medium", "Communication", "2024", ["quality", "CI/CD"]),
        item(c, "Present a technical decision you made to a non-technical stakeholder.",
             "Focus on problem, options, tradeoffs in plain language, business impact (cost, time, risk), and recommendation with success metrics.",
             "Tests clarity and stakeholder management.",
             "Medium", "Communication", "2025", ["stakeholders"]),
        item(c, "Detect a cycle in a linked list.",
             "Floyd's tortoise-hare: slow moves 1, fast moves 2; cycle if they meet. Start detection: reset slow to head, move both 1 step until equal.",
             "Standard FAANG / product company DSA.",
             "Medium", "DSA", "2024", ["linked list", "two pointers"]),
        item(c, "Merge intervals from a list of meetings.",
             "Sort by start, merge if current.start <= prev.end else append. Time O(n log n), space O(n) for output.",
             "Common scheduling interview problem.",
             "Medium", "DSA", "2024", ["intervals", "sorting"]),
        item(c, "Binary search on answer: minimum capacity to ship packages in D days.",
             "Search capacity range [max(w), sum(w)]; feasibility = greedy days needed. O(n log sum).",
             "Binary search pattern popular in 2024 interviews.",
             "Hard", "DSA", "2025", ["binary search"]),
        item(c, "SQL vs NoSQL — when would you choose each?",
             "SQL for ACID transactions, joins, reporting. NoSQL for flexible schema, horizontal scale, high write throughput. Mention specific engines used at scale.",
             "Database fundamentals for most roles.",
             "Easy", "Technical", "2024", ["SQL", "NoSQL"]),
        item(c, "Explain OAuth 2.0 authorization code flow.",
             "User → auth server login → auth code → backend exchanges code + client secret for tokens → access API with bearer token; refresh token rotation for security.",
             "Security question for web/backend interviews.",
             "Medium", "Technical", "2025", ["OAuth", "security"]),
        item(c, "What are microservices tradeoffs vs monolith?",
             "Microservices: independent deploy, team autonomy, network complexity, observability needs. Monolith: simpler ops early, modular monolith as middle ground.",
             "Architecture discussion for mid/senior candidates.",
             "Medium", "System Design", "2024", ["microservices"]),
    ]


# ─── Company-specific questions (2024–2025 hiring trends) ───
COMPANY_SPECIFIC = {
    "Google": [
        item("Google", "Design Google Search autocomplete.", "Trie or prefix index + top-k cache, debounce client, rank by popularity/freshness, fanout to shard services, latency p99 < 100ms.", "System design for search UX.", "Hard", "System Design", "2025"),
        item("Google", "Find median of two sorted arrays in O(log(m+n)).", "Binary search partition on smaller array; ensure max(left) <= min(right).", "Classic Google hard DSA.", "Hard", "DSA", "2024"),
        item("Google", "Tell me about a time you showed 'Googliness'.", "Collaboration, bias for users, intellectual humility, and doing the right thing — use STAR with measurable outcome.", "Culture / behavioral fit.", "Medium", "Behavioral", "2024"),
        item("Google", "How does MapReduce process large datasets?", "Map emits key-value pairs, shuffle groups keys, reduce aggregates; discuss stragglers and combiners.", "Big data fundamentals.", "Medium", "Technical", "2024"),
        item("Google", "Implement LRU cache O(1) get/put.", "HashMap + doubly linked list; move accessed node to head.", "Very common Google coding question.", "Medium", "DSA", "2024"),
    ],
    "Amazon": [
        item("Amazon", "Walk through Amazon's Leadership Principle 'Customer Obsession'.", "Start with customer problem, work backwards, validate with data, example where you prioritized user impact over short-term revenue.", "LP-based behavioral.", "Medium", "Behavioral", "2024"),
        item("Amazon", "Design Amazon checkout for peak sale events.", "Cart service, inventory reservation, idempotent payments, queue for order creation, CDN for static assets, auto-scale on metrics.", "High-scale retail design.", "Hard", "System Design", "2025"),
        item("Amazon", "K closest points to origin.", "Max-heap size k or quickselect; O(n log k).", "Heap pattern in Amazon loops.", "Medium", "DSA", "2024"),
        item("Amazon", "Explain AWS S3 durability model.", "Objects replicated across AZs, versioning, lifecycle policies, pre-signed URLs.", "Cloud knowledge for AWS-heavy teams.", "Medium", "Technical", "2024"),
        item("Amazon", "Tell me about a time you 'Disagreed and Committed'.", "Respectfully challenged decision with data, then fully executed after alignment.", "Core LP story.", "Medium", "Behavioral", "2025"),
    ],
    "Microsoft": [
        item("Microsoft", "Design OneDrive file sync.", "Chunk files, content-hash dedup, conflict resolution, metadata DB, delta sync, offline queue.", "Microsoft product-aligned design.", "Hard", "System Design", "2025"),
        item("Microsoft", "Explain virtual memory and paging.", "MMU maps virtual→physical pages; page faults load from disk; TLB speeds lookup.", "OS fundamentals for Azure teams.", "Medium", "Technical", "2024"),
        item("Microsoft", "Group Anagrams.", "Sort each string or count chars as key; bucket in hash map.", "Common OA / phone screen.", "Easy", "DSA", "2024"),
        item("Microsoft", "Why Azure over competitors for enterprise?", "Hybrid identity, compliance certifications, Microsoft ecosystem integration, enterprise support.", "Role-specific HR/technical.", "Easy", "HR", "2024"),
        item("Microsoft", "Describe growth mindset with an example.", "Sought feedback after bug, learned new tool, improved team doc/process.", "Microsoft culture keyword.", "Medium", "Behavioral", "2024"),
    ],
    "Meta": [
        item("Meta", "Design Facebook News Feed ranking.", "Candidate generation, scoring (engagement, quality), diversity rules, real-time features, online experiments.", "Meta-specific system design.", "Hard", "System Design", "2025"),
        item("Meta", "Serialize/deserialize binary tree.", "BFS with null markers or preorder with indices; discuss JSON vs compact format.", "Tree DSA at Meta.", "Medium", "DSA", "2024"),
        item("Meta", "Tell me about building something from 0 to 1.", "STAR with scope, speed, ambiguity, metrics of adoption.", "Entrepreneurial behavioral.", "Medium", "Behavioral", "2024"),
        item("Meta", "What is eventual consistency in distributed systems?", "Replicas converge over time; read-your-writes, conflict resolution (LWW, CRDT).", "Distributed systems for infra roles.", "Medium", "Technical", "2025"),
        item("Meta", "Minimum remove to make valid parentheses.", "Stack open indices; unmatched opens/closes; greedy removal count.", "String DSA variant.", "Medium", "DSA", "2024"),
    ],
    "Netflix": [
        item("Netflix", "Design video streaming CDN strategy.", "Encode multiple bitrates, segment HLS/DASH, edge caches, adaptive bitrate, central origin, regional failover.", "Core Netflix domain.", "Hard", "System Design", "2025"),
        item("Netflix", "Tell me about radical candor you gave or received.", "Direct feedback, no personal attacks, behavior change and outcome.", "Culture fit.", "Medium", "Behavioral", "2024"),
        item("Netflix", "Top K frequent titles in a viewing window.", "Hash count + min-heap k or bucket sort.", "Data-heavy DSA.", "Medium", "DSA", "2024"),
        item("Netflix", "How does chaos engineering improve reliability?", "Inject failures (latency, instance kill), validate fallbacks, game days, SLO monitoring.", "Netflix engineering culture.", "Medium", "Technical", "2025"),
        item("Netflix", "Explain freedom & responsibility in teams.", "High trust, high accountability, context not control — tie to personal example.", "Values alignment.", "Easy", "HR", "2024"),
    ],
    "Uber": [
        item("Uber", "Design real-time ride matching.", "Geo index (quadtree/geohash), driver supply stream, ETA model, dispatch scoring, surge pricing inputs.", "Uber core flow.", "Hard", "System Design", "2025"),
        item("Uber", "Find shortest path with traffic weights.", "Dijkstra or A* with heuristic; precompute clusters for scale.", "Graphs for maps team.", "Hard", "DSA", "2024"),
        item("Uber", "Tell me about improving marketplace fairness.", "Balance rider wait vs driver earnings; metrics; experiment results.", "Product + behavioral.", "Medium", "Behavioral", "2025"),
        item("Uber", "Explain surge pricing ethically and technically.", "Demand/supply ratio, caps, transparency, ML forecasts, avoid discrimination.", "Business + tech.", "Medium", "Communication", "2024"),
        item("Uber", "Implement thread-safe in-memory geospatial index.", "Partition by city, read-write locks, TTL for driver locations.", "Practical backend.", "Hard", "Technical", "2025"),
    ],
    "Adobe": [
        item("Adobe", "Design collaborative document editing (like Figma-lite).", "OT/CRDT for ops, WebSocket rooms, snapshot + op log, permission model.", "Creative cloud collaboration.", "Hard", "System Design", "2025"),
        item("Adobe", "Parse and evaluate simple CSS selectors on DOM.", "Tokenize selector, traverse tree, specificity rules.", "Frontend depth.", "Medium", "Technical", "2024"),
        item("Adobe", "LRU cache for asset thumbnails.", "HashMap + DLL; CDN cache headers.", "Performance focus.", "Medium", "DSA", "2024"),
        item("Adobe", "Why Adobe Creative Cloud ecosystem?", "Integrated workflows, subscription model, AI features (Firefly), enterprise accounts.", "HR motivation.", "Easy", "HR", "2024"),
        item("Adobe", "Accessibility in UI components — your approach?", "Semantic HTML, ARIA, keyboard nav, contrast, screen reader testing.", "Inclusive design.", "Medium", "Communication", "2025"),
    ],
    "PayPal": [
        item("PayPal", "Design idempotent payment API.", "Idempotency-Key header, store request hash, return same response on retry, ledger double-entry.", "Fintech correctness.", "Hard", "System Design", "2025"),
        item("PayPal", "Detect fraud patterns in transactions.", "Rules + ML features (velocity, geo, device), real-time scoring, false positive handling.", "Risk tech.", "Hard", "Technical", "2024"),
        item("PayPal", "Explain PCI-DSS scope reduction.", "Tokenization, hosted fields, no raw card storage on merchant servers.", "Compliance question.", "Medium", "Technical", "2024"),
        item("PayPal", "Two-phase commit vs Saga for payments.", "2PC strong consistency but blocking; Saga compensating transactions for microservices.", "Distributed transactions.", "Hard", "System Design", "2025"),
        item("PayPal", "Tell me about handling a production payment incident.", "Detect alerts, freeze risky traffic, root cause, customer comms, postmortem.", "Operational excellence.", "Medium", "Behavioral", "2024"),
    ],
    "Flipkart": [
        item("Flipkart", "Design flash sale inventory system.", "Reservation tokens, Redis decr with limits, queue checkout, oversell prevention, waitlist.", "India e-commerce peak load.", "Hard", "System Design", "2025"),
        item("Flipkart", "Explain CAP in context of catalog service.", "Partition tolerance required; choose CP for inventory vs AP for browse with sync.", "Practical tradeoff.", "Medium", "System Design", "2024"),
        item("Flipkart", "Search suggestions for Indian language queries.", "Normalize script, phonetic fuzzy match, popular queries trie.", "Localization.", "Medium", "Technical", "2025"),
        item("Flipkart", "Tell me about optimizing mobile app performance on low-end devices.", "Image compression, lazy load, reduce bundle, network caching.", "Mobile-first India market.", "Medium", "Behavioral", "2024"),
        item("Flipkart", "Count islands in 2D grid.", "DFS/BFS or union-find; O(mn).", "Standard DSA.", "Medium", "DSA", "2024"),
    ],
    "Zoho": [
        item("Zoho", "Design multi-tenant SaaS CRM module.", "Tenant_id on all rows, schema per tenant vs shared, RBAC, audit logs.", "Zoho product stack.", "Hard", "System Design", "2025"),
        item("Zoho", "Explain Java garbage collection tuning.", "G1/ZGC, heap sizing, GC logs, avoid memory leaks in long-lived caches.", "Common for Chennai stack.", "Medium", "Technical", "2024"),
        item("Zoho", "Build a calendar scheduling API without double booking.", "DB unique constraint on (resource, slot), transactions, timezone handling.", "Product feature design.", "Medium", "Technical", "2025"),
        item("Zoho", "Why Zoho's bootstrapped culture appeals to you?", "Product ownership, full-stack exposure, long-term R&D.", "HR fit.", "Easy", "HR", "2024"),
        item("Zoho", "Implement undo stack for a text editor.", "Two stacks undo/redo; O(1) push/pop.", "Classic OA.", "Medium", "DSA", "2024"),
    ],
    "IBM": [
        item("IBM", "Explain hybrid cloud strategy for enterprise clients.", "On-prem + IBM Cloud + Red Hat OpenShift, workload placement, compliance.", "IBM consulting angle.", "Medium", "Technical", "2025"),
        item("IBM", "Design mainframe-to-cloud migration approach.", "Assess COBOL deps, strangler fig, data replication, rollback plan.", "Legacy modernization.", "Hard", "System Design", "2024"),
        item("IBM", "What is watsonx / Gen AI governance?", "Model lineage, bias checks, PII filtering, human review loops.", "2024 AI focus.", "Medium", "Technical", "2025"),
        item("IBM", "Tell me about client-facing technical consulting.", "Listen, translate business to architecture, POC, roadmap, KPIs.", "Consulting behavioral.", "Medium", "Behavioral", "2024"),
        item("IBM", "Rotate matrix 90 degrees in-place.", "Transpose + reverse rows; O(n^2).", "DSA screening.", "Medium", "DSA", "2024"),
    ],
    "Accenture": [
        item("Accenture", "How do you run a discovery workshop for digital transformation?", "Stakeholders, as-is process, pain points, prioritization matrix, roadmap.", "Consulting method.", "Medium", "Communication", "2025"),
        item("Accenture", "Explain Agile vs Waterfall for government projects.", "Regulatory gates, hybrid models, sprint demos, contract milestones.", "Delivery models.", "Easy", "HR", "2024"),
        item("Accenture", "Design CI/CD for regulated banking client.", "Separate envs, approvals, artifact signing, audit trail, automated tests.", "Enterprise delivery.", "Hard", "System Design", "2024"),
        item("Accenture", "Tell me about managing offshore-onshore teams.", "Overlap hours, clear RACI, documentation, cultural sensitivity.", "Global delivery.", "Medium", "Behavioral", "2024"),
        item("Accenture", "SQL: find second highest salary per department.", "DENSE_RANK() or subquery MAX < dept.", "Classic Accenture SQL.", "Medium", "DSA", "2024"),
    ],
    "Deloitte": [
        item("Deloitte", "Describe risk assessment in a technology audit.", "Identify controls, test design, sampling, findings severity, remediation tracking.", "Audit/consulting track.", "Medium", "Technical", "2024"),
        item("Deloitte", "Explain zero-trust security architecture.", "Verify explicitly, least privilege, micro-segmentation, continuous monitoring.", "Cyber hiring trend 2025.", "Medium", "Technical", "2025"),
        item("Deloitte", "Case: client wants GenAI chatbot on internal docs.", "RAG pipeline, vector DB, access control, hallucination mitigation, cost model.", "2024–2025 hot topic.", "Hard", "System Design", "2025"),
        item("Deloitte", "Tell me about ethical dilemma at work.", "Confidentiality, escalation path, outcome without violating policy.", "Professionalism.", "Medium", "Behavioral", "2024"),
        item("Deloitte", "Write pseudocode for detecting duplicate invoices.", "Hash vendor+amount+date; fuzzy match threshold; flag for review.", "Practical problem solving.", "Medium", "DSA", "2024"),
    ],
    "Capgemini": [
        item("Capgemini", "Explain SAP S/4HANA migration considerations.", "Data cleansing, downtime window, integration testing, cutover plan.", "ERP consulting.", "Medium", "Technical", "2024"),
        item("Capgemini", "Design API gateway for microservices client.", "Auth, rate limit, routing, observability, versioning.", "Integration architecture.", "Hard", "System Design", "2025"),
        item("Capgemini", "Java: difference between HashMap and ConcurrentHashMap.", "Thread safety, segments, fail-fast vs weakly consistent iterators.", "Backend screening.", "Easy", "Technical", "2024"),
        item("Capgemini", "Tell me about working with European clients.", "Time zones, GDPR awareness, formal communication, documentation.", "Global delivery.", "Medium", "Communication", "2024"),
        item("Capgemini", "Find missing number in 1..n array.", "Sum formula n(n+1)/2 - sum(arr) or XOR trick.", "OA DSA.", "Easy", "DSA", "2024"),
    ],
    "TCS": [
        item("TCS", "Explain Software Development Life Cycle phases.", "Requirements, design, coding, testing, deployment, maintenance; mention Agile ceremonies.", "TCS fresher/ lateral staple.", "Easy", "HR", "2024"),
        item("TCS", "Java OOP pillars with examples.", "Encapsulation, inheritance, polymorphism, abstraction; SOLID brief.", "Core Java screening.", "Easy", "Technical", "2024"),
        item("TCS", "SQL: INNER vs LEFT JOIN.", "INNER returns matches only; LEFT keeps all left rows with NULLs for non-match.", "Database basics.", "Easy", "Technical", "2024"),
        item("TCS", "What is digital transformation in banking for TCS?", "Core modernization, API layers, cloud migration, regulatory compliance.", "Domain awareness.", "Medium", "Communication", "2025"),
        item("TCS", "Reverse words in a sentence.", "Split, reverse list, join; O(n).", "Coding test common question.", "Easy", "DSA", "2024"),
    ],
    "Infosys": [
        item("Infosys", "Explain Infosys Topaz / GenAI offerings at high level.", "Enterprise AI stack, responsible AI, integration with client data.", "2024–2025 Infosys focus.", "Medium", "HR", "2025"),
        item("Infosys", "Spring Boot: how dependency injection works.", "@Component scanning, constructor injection preferred, bean scopes.", "Java role screening.", "Medium", "Technical", "2024"),
        item("Infosys", "Describe test pyramid for microservices.", "Many unit, contract tests, fewer E2E; mocks for external deps.", "QA + dev knowledge.", "Medium", "Technical", "2024"),
        item("Infosys", "Tell me about adapting to new project mid-assignment.", "Quick ramp, shadowing, documentation, deliver small win early.", "Behavioral.", "Medium", "Behavioral", "2024"),
        item("Infosys", "Check if string is palindrome ignoring case.", "Two pointers sanitize alphanumeric; O(n).", "OA question.", "Easy", "DSA", "2024"),
    ],
    "Wipro": [
        item("Wipro", "Explain cloud migration 6R strategies.", "Rehost, replatform, refactor, repurchase, retire, retain — pick based on app criticality.", "Wipro cloud practice.", "Medium", "Technical", "2024"),
        item("Wipro", "What is DevSecOps?", "Shift-left security scans in CI, SAST/DAST, secrets management, policy as code.", "Modern delivery.", "Medium", "Technical", "2025"),
        item("Wipro", "Handle conflict with client on scope creep.", "Change request process, impact analysis, timeline/cost tradeoff, documented sign-off.", "Client management.", "Medium", "Behavioral", "2024"),
        item("Wipro", "Explain REST status codes 200, 201, 400, 401, 404, 500.", "Success, created, bad request, unauthorized, not found, server error.", "API basics.", "Easy", "Technical", "2024"),
        item("Wipro", "Fibonacci with dynamic programming.", "Bottom-up O(n) time O(1) space.", "DSA screening.", "Easy", "DSA", "2024"),
    ],
    "Cognizant": [
        item("Cognizant", "Explain healthcare HIPAA considerations in software.", "PHI encryption, access logs, BAA agreements, minimum necessary principle.", "Cognizant healthcare vertical.", "Medium", "Technical", "2024"),
        item("Cognizant", "Design patient appointment scheduling API.", "Avoid double booking, reminders, EMR integration, audit trail.", "Domain design.", "Hard", "System Design", "2025"),
        item("Cognizant", "Tell me about working in Agile distributed teams.", "Daily standups, Jira hygiene, sprint demos, retro actions.", "Delivery behavioral.", "Easy", "Behavioral", "2024"),
        item("Cognizant", "Explain indexing in relational databases.", "B-tree indexes, covering indexes, when not to index (write-heavy).", "DB performance.", "Medium", "Technical", "2024"),
        item("Cognizant", "Valid parentheses using stack.", "Push opens, pop on match; O(n).", "Classic DSA.", "Easy", "DSA", "2024"),
    ],
    "Tech Mahindra": [
        item("Tech Mahindra", "Explain 5G network slicing for enterprise.", "Isolated logical networks on shared infra, SLA per slice, use cases IoT/enterprise.", "Telecom domain.", "Medium", "Technical", "2025"),
        item("Tech Mahindra", "Design IoT telemetry ingestion pipeline.", "MQTT broker, stream processing, time-series DB, alerting rules.", "IoT practice.", "Hard", "System Design", "2024"),
        item("Tech Mahindra", "Tell me about telecom client delivery challenges.", "Strict SLAs, change windows, regression suites, compliance docs.", "Behavioral.", "Medium", "Behavioral", "2024"),
        item("Tech Mahindra", "Explain OSI model layers briefly.", "Physical→Application; map HTTP/TCP/IP to layers.", "Networking basics.", "Easy", "Technical", "2024"),
        item("Tech Mahindra", "Find maximum subarray sum (Kadane).", "Track current and global max; O(n).", "DSA.", "Medium", "DSA", "2024"),
    ],
    "HCL": [
        item("HCL", "Explain HCL's Mode 1-2-3 innovation framework.", "Core modernization, growth areas, new products — align career story.", "Company-specific HR.", "Easy", "HR", "2024"),
        item("HCL", "Design logging and monitoring for global app.", "Structured logs, trace IDs, metrics (Prometheus), dashboards, on-call runbooks.", "Ops excellence.", "Hard", "System Design", "2025"),
        item("HCL", "Java: checked vs unchecked exceptions.", "Checked must declare/handle; unchecked RuntimeException for programming errors.", "Java interview staple.", "Easy", "Technical", "2024"),
        item("HCL", "Tell me about knowledge transfer before leaving a project.", "Documentation, pairing, recorded demos, transition checklist.", "Professional conduct.", "Medium", "Behavioral", "2024"),
        item("HCL", "Implement binary search on sorted array.", "l,r mid compare, O(log n).", "DSA.", "Easy", "DSA", "2024"),
    ],
}


def build_all_questions():
    """Merge shared pool + company-specific; ensure 20+ per company."""
    all_questions = []
    seen = set()

    for company in COMPANIES:
        name = company["name"]
        batch = shared_pool(name) + COMPANY_SPECIFIC.get(name, [])

        # Deduplicate by (company, question text)
        company_count = 0
        for q in batch:
            key = (q["company_name"].lower(), q["question"].lower().strip())
            if key in seen:
                continue
            seen.add(key)
            all_questions.append(q)
            company_count += 1

        if company_count < 20:
            raise ValueError(f"{name} has only {company_count} questions (need 20+)")

    return all_questions


def main():
    questions = build_all_questions()
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "interview_questions.json")

    payload = {
        "version": "2025.1",
        "generated_for": [c["name"] for c in COMPANIES],
        "total": len(questions),
        "questions": questions,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    counts = {}
    for q in questions:
        counts[q["company_name"]] = counts.get(q["company_name"], 0) + 1

    print(f"Wrote {len(questions)} questions to {out_path}")
    for name in sorted(counts):
        print(f"  {name}: {counts[name]}")


if __name__ == "__main__":
    main()
