"""The scoring engine: demand (measured from trending) minus supply (measured from search).

Two independent scarcity signals, because they fail in different ways:

  * topic scarcity  — the topic is trending, yet few repositories carry it
  * registry vacancy — the phrase returns only the popularity floor, meaning nothing in the
                       skill registry semantically matches it

Neither is proof of a market. Trending measures attention, not willingness to pay. The score
ranks *where to look*, and the report says so.
"""
from __future__ import annotations

import math
import time

from . import api

# Pure ecosystem tags and generic resource words: they are labels, not niches, and would
# drown the signal. A trending "awesome-list" repo contributes nothing usable here.
STOPLIST = {
    "python", "javascript", "typescript", "go", "rust", "java", "c", "cpp", "shell",
    "cli", "api", "ai", "llm", "machine-learning", "deep-learning", "web", "app",
    "open-source", "hacktoberfest", "framework", "library", "tool", "tools",
    "automation", "productivity", "developer-tools", "frontend", "backend", "database",
    "book", "books", "tutorial", "tutorials", "course", "courses", "guide", "guides",
    "awesome", "awesome-list", "learning", "education", "study", "notes", "blog",
    "resources", "interview", "cheatsheet", "roadmap", "docs", "documentation",
    "algo", "algorithm", "algorithms", "data-structure", "data-structures",
}

_PACE_EVERY = 8
_PACE_SLEEP = 4.0
TOPICS_PER_REPO = 3  # one repo must not monopolise the board


def _pace(i: int) -> None:
    if i and i % _PACE_EVERY == 0:
        time.sleep(_PACE_SLEEP)


def collect(since: str = "daily", extra_since: str = "weekly") -> dict:
    """Pull every bucket into one repo registry with demand features attached."""
    board = {}
    for bucket in api.BUCKETS:
        for e in api.fetch_trending(bucket, since):
            r = board.setdefault(e["repo"], {"repo": e["repo"], "desc": e["desc"],
                                             "stars": 0, "buckets": set(), "weekly": False})
            r["stars"] = max(r["stars"], e["stars"] or 0)
            r["buckets"].add(bucket)
            if e["desc"] and not r["desc"]:
                r["desc"] = e["desc"]

    # A repo that also shows up on the weekly board is a trend, not a one-day spike.
    weekly = set()
    for bucket in ("global", "zh"):
        for e in api.fetch_trending(bucket, extra_since):
            weekly.add(e["repo"])
    for name, r in board.items():
        r["weekly"] = name in weekly
    return board


def demand_scores(board: dict) -> dict:
    """Normalise velocity inside each bucket, then blend with breadth and persistence."""
    top: dict[str, int] = {}
    for r in board.values():
        for b in r["buckets"]:
            top[b] = max(top.get(b, 0), r["stars"])
    out = {}
    for name, r in board.items():
        vel = max((r["stars"] / top[b]) for b in r["buckets"] if top.get(b))
        breadth = (len(r["buckets"]) - 1) / max(1, len(api.BUCKETS) - 1)
        persist = 1.0 if r["weekly"] else 0.0
        out[name] = round(0.6 * vel + 0.25 * breadth + 0.15 * persist, 4)
    return out


def _percentile_rank(values: list[int]) -> list[float]:
    """0 = smallest count, 1 = largest. Used so scarcity is relative, not an absolute guess."""
    n = len(values)
    if n <= 1:
        return [0.0] * n
    order = sorted(range(n), key=lambda i: values[i])
    rank = [0.0] * n
    for pos, i in enumerate(order):
        rank[i] = pos / (n - 1)
    return rank


def scan(limit_per_bucket: int = 12, max_topics: int = 18, check_registry: bool = True,
         since: str = "daily") -> dict:
    board = collect(since)
    demand = demand_scores(board)

    # Only the strongest repos contribute topics — otherwise the tail pollutes the signal.
    ranked = sorted(board.values(), key=lambda r: -demand[r["repo"]])[:limit_per_bucket]
    topics: dict[str, dict] = {}
    for i, r in enumerate(ranked):
        _pace(i)
        try:
            info = api.repo(r["repo"])
        except RuntimeError:
            continue
        for t in (info.get("topics") or [])[:TOPICS_PER_REPO]:
            t = t.lower()
            if t in STOPLIST:
                continue
            slot = topics.setdefault(t, {"topic": t, "repos": [], "best": 0.0,
                                         "best_stars": 0, "best_buckets": []})
            slot["repos"].append(r["repo"])
            if demand[r["repo"]] > slot["best"]:
                slot["best"] = demand[r["repo"]]
                slot["best_stars"] = r["stars"]
                slot["best_buckets"] = sorted(r["buckets"])

    # Cap before spending search quota; keep the ones with the strongest demand.
    picked = sorted(topics.values(), key=lambda s: -s["best"])[:max_topics]

    counts = []
    for i, s in enumerate(picked):
        _pace(i)
        try:
            st = api.topic_stats(s["topic"])
        except RuntimeError:
            st = {"count": None, "top_stars": 0, "top_repo": None}
        s["topic_repos"] = st["count"]
        s["top_stars"] = st["top_stars"]
        s["top_repo"] = st["top_repo"]
        counts.append(st["count"] if st["count"] is not None else 10 ** 6)

    pct = _percentile_rank(counts)
    for s, p in zip(picked, pct):
        s["supply_percentile"] = round(p, 3)
        # Percentile alone would hand a perfect score to "the least bad of a bad set" — with
        # six topics, the smallest always ranks 1.0 however crowded it is. Blend in an absolute
        # term so 351 repos still reads as crowded.
        n = s.get("topic_repos")
        absolute = 1 / (1 + (n if n else 10 ** 6) / 100)
        s["supply_absolute"] = round(absolute, 3)
        # Dominance: a 28-repo topic whose leader has 95k stars is NOT a vacancy. Counting
        # repositories alone ranked exactly that as the best opportunity on 2026-10-17, because
        # the leader was the trending repo that produced the topic in the first place.
        occupancy = min(1.0, math.log10((s.get("top_stars") or 0) + 1) / 4)
        s["occupancy"] = round(occupancy, 3)
        s["supply_gap"] = round((0.5 * (1 - p) + 0.5 * absolute) * (1 - 0.75 * occupancy), 3)

    if check_registry:
        for i, s in enumerate(picked):
            phrase = s["topic"].replace("-", " ")
            s["registry"] = api.skillhub_probe(phrase)
            _pace(i)
    else:
        for s in picked:
            s["registry"] = {"top_score": None, "has_match": None}

    for s in picked:
        reg_gap = 1.0 if s["registry"].get("has_match") is False else 0.0
        s["registry_gap"] = reg_gap
        s["score"] = round(100 * s["best"] * (0.65 * s["supply_gap"] + 0.35 * reg_gap), 1)

    picked.sort(key=lambda s: -s["score"])
    return {
        "since": since,
        "buckets": api.BUCKETS,
        "repos_scanned": len(board),
        "topics_scanned": len(picked),
        "floors": {b: api.bucket_stats(api.fetch_trending(b, since)) for b in ("global", "zh")},
        "opportunities": picked,
    }
