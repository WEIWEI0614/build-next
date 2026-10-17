<div align="center">

# 🧭 build-next

**What to build next — measured as demand minus supply.**
Reads the live GitHub Trending boards and a skill-registry search index, then ranks the niches
where attention is rising but supply is thin.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deps](https://img.shields.io/badge/runtime%20deps-0-brightgreen)](pyproject.toml)
[![No LLM](https://img.shields.io/badge/LLM-not%20required-success)]()

[English](README.md) · [简体中文](README.zh-CN.md)

**Live scan →** [中文](https://weiwei0614.github.io/build-next/) · [English](https://weiwei0614.github.io/build-next/en.html)

</div>

---

## The problem with "what should I build"

Ask ten people and you get ten opinions, all shaped by whatever they happened to see last week.
This tool replaces the opinion with two numbers you can re-measure yourself:

```
opportunity ≈ demand (attention, measured from trending)
            − supply (crowdedness, measured from repo counts and registry hits)
```

## What it actually finds

A real run, 2026-10-17:

```
topic                            score  demand   repos    leader  registry
agent-ide                        33.8  0.6833      28   ★95009   vacant
ocr-python                       21.9  0.5062     621   ★47983   vacant
data-collection                  20.3  0.4969    1873   ★44700   vacant
asyncio                           2.2  0.4969    7661  ★103166   has hits
ai-agents                         0.0  0.6833  120832  ★302066   has hits
```

Four columns, and you need all four:

- **score** — sort key only. Never a verdict.
- **repos** — absolute supply.
- **leader** — stars of the biggest repo in that topic. **This is the column that saves you.**
- **registry** — `vacant` means nothing in the skill registry semantically matches the phrase.

The last row is the product: `ai-agents` has the **same demand** as `agent-ide` (both triggered by
the same trending repo) and scores zero, because 120k repositories carry it.

And the first row is the lesson: `agent-ide` has only **28 repositories**, looks vacant, and its
leader has **95,009 stars — the very repo that put it on the trending board.** Counting
repositories without counting their size recommended building an agent IDE against a 95k-star
incumbent. The dominance term exists because that happened, not because it was elegant.

## The limitation that matters

Every topic here was harvested from a trending repo, so by construction it is a space that repo
already occupies. That is why nothing scored above 34. **Real gaps live adjacent, not identical:**
a 47k-star OCR project says document parsing is solved — it says nothing about the editable
table-review step after parsing, which has no topic tag and never appears in a scan.

The tool measures attention. Inferring what is missing *next to* it is a language task, and this
project refuses to fake it with a heuristic.

## Two signals, two distinct ways to be wrong

| Signal | How it's measured | How it misleads |
|---|---|---|
| **Topic scarcity** | repository count for a trending repo's topic | few repos may just mean *nobody tags with it*, not nobody builds it |
| **Registry vacancy** | query the skill registry; only floor scores (<0.055) means no semantic match | a vacancy may mean *nobody wants it*, not nobody supplies it |

Both describe supply. **Neither proves demand.** Trending measures attention — not willingness
to pay, not retention. The report prints this every time.

## Quick start

```bash
pip install build-next        # or: pip install -e .
```

```bash
buildnext scan --limit 10 --max-topics 14 --md brief.md --site docs
```

| flag | meaning |
|---|---|
| `--limit` | how many trending repos per bucket to deep-scan (default 12) |
| `--max-topics` | cap on topic lookups; bounded by GitHub's 30 req/min search quota |
| `--md` | write an agent-ready brief |
| `--site` | write both languages into a directory |
| `--json` | machine-readable output |
| `--no-registry` | skip the skill-registry probe |

A full run takes 1–3 minutes — it is making dozens of live API calls, paced on purpose.

## Validate before you recommend

Scarcity alone is not an opportunity. Always check who already occupies the topic:

```bash
gh api "search/repositories?q=topic:agent-ide&sort=stars&per_page=10" \
  --jq '.items[] | "\(.full_name) ★\(.stargazers_count) — \(.description)"'
```

If the top results are mature projects with hundreds of stars, supply is not thin — the tag
is just underused. Only 0–5 star projects (or an empty page) indicate a real vacancy.

`SKILL.md` encodes this as a mandatory step before any recommendation is written.

## Tool measures, agent imagines

The CLI deliberately stops at evidence. Turning it into "make this, for these people, because
of these numbers" is a judgement call — so `SKILL.md` hands that to an agent and specifies what
each proposal must contain (audience, problem, why-now with a cited number, smallest viable
version, biggest risk). Rule engines are bad at imagination; this one doesn't pretend.

## Use it as an agent skill

```bash
cp -r . ~/.workbuddy/skills/build-next
```

Then ask *"what should I build"* — or run it on a schedule for a daily board.

## Honest limits

- Trending is a **momentum** board, not a market study. A niche can be trending and worthless.
- Topic tags are user-generated and inconsistent; the stoplist filters ecosystem tags, but
  noise remains.
- Scores are only comparable **within one run**. Percentiles are computed from that run's
  candidate set, so do not diff scores across days — diff the membership instead.

## License

MIT. Re-measure rather than trust this file.
