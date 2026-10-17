---
name: build-next
description: Recommend what to build next by measuring demand against supply — reads the live GitHub Trending boards and a skill-registry search index, then ranks niches where attention is rising but supply is thin. Use when the user asks "what should I build", "what's a good side project", "find me an underserved niche", "what's trending and what's missing", "帮我推荐做什么项目", or wants daily project ideas grounded in data rather than opinion. The CLI produces evidence; the proposals are written by you from that evidence.
description_zh: "按「需求减供给」推荐该做什么项目：读热榜实测注意力，读注册表实测供给空缺"
description_en: "Recommend what to build next by measuring demand minus supply"
---

# build-next

绝大多数「做什么项目」的建议，本质是随口一说。这个 skill 把它拆成两个**可测量**的量：

```
机会 ≈ 需求（热榜实测的注意力）  −  供给（仓库数与注册表命中实测的拥挤度）
```

工具只产出**证据**。**建议由你根据证据来写**——这是刻意的分工：规则适合测量，不适合想象。

## When to use

- 「我该做什么项目」「有什么值得做的 side project」「找个还没被做烂的方向」
- 用户想跟踪每日趋势并从中找机会
- 用户拿到一堆 trending 列表，但不知道哪条对自己有用

## 两个信号，各自会怎么骗你

| 信号 | 怎么测 | 会怎么骗你 |
|---|---|---|
| **话题稀缺** | trending 仓库的 topic，其仓库总数越少越稀缺 | topic 少可能只是因为**没人用它打标签**，不代表没人做这件事 |
| **注册表空位** | 用 topic 当查询词打技能注册表，返回只有地板分（<0.055）说明没有语义命中 | 空位可能意味着**没有需求**，而不是没人满足 |

两个信号都指向「供给薄」，但**都不证明有需求**。热榜证明的是注意力，不是付费意愿，更不是留存。报告里必须带上这句，不要省。

## Workflow

### 1. 扫描

```bash
buildnext scan --limit 10 --max-topics 14 --md brief.md --site docs
```

- `--limit` 每个分桶深挖几个 trending 仓库（默认 12）。调大更全面，但更慢。
- `--max-topics` 上限，受 GitHub 搜索配额约束（30 req/min，工具已内置限速）。
- `--md` 输出 agent 可读的结构化简报；`--site` 出中英双语页面。
- 耗时约 1–3 分钟，取决于上限。

输出形如：

```
主题词                           机会分      需求     仓库数  注册表
agent-ide                       63.5  0.6833      28  空位   ← stablyai/orca
ocr-python                      33.9  0.5062     621  空位   ← hiroi-sora/Umi-OCR
data-collection                 28.1  0.4969    1873  空位   ← Evil0ctal/...
```

三个字段都要读，缺一个就会误判：

- **机会分** — 综合排序，只看它排序，不要拿它当结论。
- **仓库数** — 供给的绝对量。28 和 1873 是两种完全不同的世界。
- **注册表** — 「空位」表示没有语义命中，是加分项；但也可能是没人搜过这个词。

### 2. 验证，别直接推荐

拿到候选 topic 之后，**先确认它到底有没有人已经做了**：

```bash
gh api "search/repositories?q=topic:<topic>&sort=stars&per_page=10" \
  --jq '.items[] | "\(.full_name) ★\(.stargazers_count) — \(.description)"'
```

- 前几名都是几百星以上的成熟项目 → **不要推荐**，供给薄只是标签没铺开。
- 前几名是 0–5 星的小项目，或者根本没几个 → 才是真空位。

这一步不能跳。跳过它就是在教用户重复造轮子。

### 3. 写建议

基于证据写 **3 个具体建议**，每个必须包含五件事：

1. **做给谁** — 具体到一类人，不是「开发者」。
2. **解决什么** — 一句话，必须能在没有工具的情况下说清。
3. **为什么是现在** — **引用扫描里的真实数字**（哪个仓库在涨、topic 几个仓库、注册表是不是空位）。
4. **最小可行版本** — 一个周末能做完的形态，不是三年规划。
5. **最大的风险** — 说真的风险，通常是「需求不存在」或「已有成熟替代」。

禁止输出：「可以做一个 X 平台」「建议关注 Y 领域」这种没有落点的句子。

### 4. 每天跑

这个 skill 是为日更设计的。建议每天同一时间扫一次，只看**新进入前几名**的 topic——连续多天在榜的，才是真趋势。

## 评分口径

```
需求  = 0.60×分桶内速度归一 + 0.25×跨分桶广度 + 0.15×是否也在周榜
供给缺口 = 0.5×(1 − 分桶内百分位) + 0.5×(1 / (1 + 仓库数/100))
机会分 = 100 × 需求 × (0.65×供给缺口 + 0.35×注册表是否空位)
```

只对**每个仓库的前 3 个 topic** 取样，否则一个 topic 特别多的仓库会垄断整张榜。
百分位与绝对量各占一半，是为了避免「六个候选里最不坏的那个」也拿满分。

完整推导见 `references/method.md`。

## Do not

- **不要把机会分当预测。** 它是排序工具，不是成功率。
- **不要推荐已经拥挤的话题**（仓库数上千），无论分数看起来多好。
- **不要跳过验证步骤**（上面第 2 步）。
- **不要编造趋势。** 所有数字必须来自本次运行，不能引用上周的。
