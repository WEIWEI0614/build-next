"""HTTP + data sources: GitHub (API and the HTML trending page) and the SkillHub registry.

Kept dependency-free on purpose — the whole value of a daily scan is that anyone can run it
without a toolchain.
"""
from __future__ import annotations

import json
import os
import re
import statistics
import subprocess
import urllib.error
import urllib.parse
import urllib.request

UA = "build-next (+https://github.com/WEIWEI0614/build-next)"
token_cache: str | None = None
_token_done = False


def _token() -> str | None:
    global token_cache, _token_done
    if _token_done:
        return token_cache
    _token_done = True
    token_cache = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token_cache:
        return token_cache
    try:
        p = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
        if p.returncode == 0 and p.stdout.strip():
            token_cache = p.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return token_cache


def _get(url: str, accept: str = "application/vnd.github+json", timeout: int = 25,
         auth: bool = True) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    if auth:
        t = _token()
        if t:
            req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, b""


def get_json(url: str) -> dict:
    code, body = _get(url)
    if code != 200:
        raise RuntimeError(f"HTTP {code}: {body[:120].decode('utf-8', 'replace')}")
    return json.loads(body)


# ---------------------------------------------------------------- GitHub: API


def repo(owner_repo: str) -> dict:
    return get_json(f"https://api.github.com/repos/{owner_repo}")


def search_count(query: str) -> int:
    q = urllib.parse.quote(query)
    d = get_json(f"https://api.github.com/search/repositories?q={q}&per_page=1")
    return int(d.get("total_count") or 0)


def topic_stats(topic: str) -> dict:
    """Repository count AND dominance in one call.

    A topic with 28 repositories is not a vacancy if one of them has 95k stars — that is an
    occupied niche with an underused tag. Sorting by stars gets both facts for the same quota.
    """
    q = urllib.parse.quote(f"topic:{topic}")
    d = get_json(f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page=5")
    items = d.get("items") or []
    top = items[0] if items else None
    return {
        "count": int(d.get("total_count") or 0),
        "top_stars": int(top.get("stargazers_count") or 0) if top else 0,
        "top_repo": top.get("full_name") if top else None,
    }


# ---------------------------------------------------------------- GitHub: trending


BASE = "https://github.com/trending"
_ROW = re.compile(r'<article class="Box-row">(.*?)</article>', re.S)
_REPO = re.compile(r"return_to=%2F([A-Za-z0-9_.-]+)%2F([A-Za-z0-9_.-]+)")
_STARS = re.compile(r"([\d,]+)\s*stars (?:today|this week|this month)")
_DESC = re.compile(r'<p class="col-9[^"]*">\s*(.*?)\s*</p>', re.S)

BUCKETS = ["global", "python", "typescript", "zh"]


def trending_url(bucket: str, since: str) -> str:
    if bucket == "global":
        return f"{BASE}?since={since}"
    if bucket in ("zh", "en"):
        return f"{BASE}?since={since}&spoken_language_code={bucket}"
    return f"{BASE}?since={since}&language={bucket}"


def fetch_trending(bucket: str = "global", since: str = "daily") -> list[dict]:
    code, body = _get(trending_url(bucket, since), accept="text/html")
    if code != 200:
        return []
    html = body.decode("utf-8", "replace")
    out, seen = [], set()
    for row in _ROW.findall(html):
        m = _REPO.search(row)
        if not m:
            continue
        name = f"{m.group(1)}/{m.group(2)}"
        if name in seen:
            continue
        seen.add(name)
        st = _STARS.search(row)
        de = _DESC.search(row)
        out.append({
            "repo": name,
            "stars": int(st.group(1).replace(",", "")) if st else None,
            "desc": re.sub(r"<[^>]+>", "", de.group(1)).strip() if de else "",
        })
    return out


def bucket_stats(entries: list[dict]) -> dict:
    vals = sorted((e["stars"] for e in entries if e["stars"] is not None), reverse=True)
    if not vals:
        return {"count": len(entries), "min": None, "median": None, "max": None}
    return {"count": len(entries), "min": vals[-1],
            "median": int(statistics.median(vals)), "max": vals[0]}


# ---------------------------------------------------------------- SkillHub


SH_SEARCH = "https://lightmake.site/api/v1/search"
SH_FLOOR = 0.055  # below this the list is a plain download ranking, i.e. nothing matched


def skillhub_probe(query: str, limit: int = 6) -> dict:
    if not (query or "").strip():
        return {"top_score": None, "has_match": False}
    url = f"{SH_SEARCH}?q={urllib.parse.quote(query)}&limit={limit}"
    try:
        code, body = _get(url, accept="application/json", auth=False)
        if code != 200:
            return {"top_score": None, "has_match": False}
        res = (json.loads(body).get("results") or [])
    except (ValueError, OSError):
        return {"top_score": None, "has_match": False}
    if not res:
        return {"top_score": 0.0, "has_match": False, "empty": True}
    top = res[0].get("score") or 0
    return {
        "top_score": round(top, 4),
        "has_match": top >= SH_FLOOR,
        "top_slug": res[0].get("slug"),
        "matches": sum(1 for r in res if (r.get("score") or 0) >= SH_FLOOR),
    }
