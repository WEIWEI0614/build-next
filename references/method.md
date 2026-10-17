# Method — how the score is built, and where it breaks

## Why two signals

A single "trending topic" ranking is useless for deciding what to build: the topics that trend
hardest are, by definition, the ones already crowded. The interesting cell is the *off-diagonal*
— attention arriving somewhere supply has not caught up.

So the score needs a demand term and a supply term measured **independently**:

- demand comes from the trending boards (velocity, breadth, persistence)
- supply comes from repository counts and a registry probe

They fail differently, which is why both are reported separately rather than pre-multiplied
into one opaque number.

## Demand

```
demand(repo) = 0.60 × velocity + 0.25 × breadth + 0.15 × persistence
```

| term | definition | why |
|---|---|---|
| **velocity** | stars in window ÷ max stars in that bucket | trending is per-bucket normalised, so raw counts across buckets are not comparable |
| **breadth** | (distinct buckets present − 1) ÷ (buckets − 1) | a repo on global + python + zh at once is a broader trend than one on a single language board |
| **persistence** | 1 if it also appears on the weekly board | separates a real trend from a one-day spike |

`demand(topic) = max(demand) over the repos carrying that topic` — a topic inherits its
strongest witness, not the average of its witnesses.

## Supply

```
absolute_scarcity = 1 / (1 + repo_count / 100)
percentile_scarcity = 1 − percentile_rank(repo_count within this run)
supply_gap = 0.5 × percentile_scarcity + 0.5 × absolute_scarcity
```

The percentile term alone is a trap: with six candidates the smallest always yields 1.0,
however crowded it actually is. Measured once with percentile only, `algo` (351 repos) scored a
perfect supply gap purely for being the least bad of six. The absolute term anchors it —
351 repos → `1/(1+3.51) = 0.22`, five repos → `0.95`.

## Registry vacancy

Query the registry with the topic as a phrase. Measured behaviour of that index (2026-10-17):
a genuine semantic match scores **≈0.060–0.110**; when nothing matches, the result list degrades
to a plain download ranking scoring **≈0.0500** and below. Two unrelated queries returned an
identical result list, which is the proof that the floor is not a match.

So `has_match = top_score ≥ 0.055`, and a vacancy contributes `1.0`, otherwise `0`.

## Combined

```
score = 100 × demand × (0.65 × supply_gap + 0.35 × registry_vacancy)
```

Weights are a judgement call, not a measurement. `supply_gap` carries more because a crowded
topic is fatal regardless of registry state; a vacant registry is a bonus, not a thesis.

## Sampling choices that materially change the output

1. **Top-3 topics per repo.** Without this cap one repo with fifteen tags monopolises the board.
   Observed: an early run returned six topics all belonging to a single trending repo.
2. **Stoplist.** Ecosystem tags (`python`, `cli`, `ai`) and generic resource tags (`book`,
   `tutorial`, `awesome-list`, `algorithm`) are removed — they are labels, not niches. Before the
   list was expanded, `data-structures` (35,147 repos) and `book` (5,708) ranked highly.
3. **Cap on topic lookups** (`--max-topics`). Each lookup is a search request; GitHub allows
   30/minute authenticated. The tool sleeps 4s every 8 requests.

## Known failure modes

| Failure | Symptom | Mitigation |
|---|---|---|
| Tag underuse read as supply gap | topic has few repos but mature projects exist | the mandatory `topic:` verification step in SKILL.md |
| Vacancy read as demand | registry has no match because nobody searches that phrase | report `top_score`; treat vacancy as a bonus only (0.35 weight) |
| Attention read as market | high demand, no willingness to pay | printed caveat in every report |
| Score drift across runs | percentiles are run-local | compare membership, never scores, across days |

## What would actually validate a niche

None of this. The score narrows the search; validation requires talking to the people who have
the problem. The tool is explicitly built to stop one step short of that, because a CLI cannot
do it and pretending otherwise would be the same folklore this project exists to replace.
