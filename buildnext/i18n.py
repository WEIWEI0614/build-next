"""Bilingual strings. Two languages, no framework; `t()` falls back to English."""
from __future__ import annotations

MSG: dict[str, dict[str, str]] = {
    "t.title": {"zh": "机会扫描", "en": "Opportunity scan"},
    "t.sub": {"zh": "需求（热榜实测）− 供给（搜索实测）", "en": "Demand (measured from trending) − supply (measured from search)"},
    "t.opps": {"zh": "按机会分排序", "en": "Ranked by opportunity score"},
    "t.topic": {"zh": "主题词", "en": "topic"},
    "t.score": {"zh": "机会分", "en": "score"},
    "t.demand": {"zh": "需求", "en": "demand"},
    "t.repos": {"zh": "仓库数", "en": "repos"},
    "t.registry": {"zh": "注册表", "en": "registry"},
    "t.trigger": {"zh": "触发来源", "en": "triggered by"},
    "t.leader": {"zh": "领先者", "en": "leader"},
    "t.buckets": {"zh": "上榜分桶", "en": "buckets"},
    "t.none": {"zh": "本次没有足够强的信号。", "en": "No signal strong enough this run."},
    "t.scanned": {"zh": "扫描了 {repos} 个上榜仓库，评估 {topics} 个主题词", "en": "Scanned {repos} trending repos, evaluated {topics} topics"},
    "t.floors": {"zh": "当次热榜门槛", "en": "Trending floors this run"},
    "t.caveat": {
        "zh": "热榜衡量的是注意力，不是付费意愿。机会分只回答「该去看哪里」，不证明有市场。",
        "en": "Trending measures attention, not willingness to pay. The score says where to look; it does not prove a market.",
    },
    "t.vacant": {"zh": "空位", "en": "vacant"},
    "t.has_hits": {"zh": "已有命中", "en": "has matches"},
    "t.unknown": {"zh": "未测", "en": "not probed"},
    "t.method": {"zh": "口径", "en": "Method"},

    "b.title": {"zh": "机会简报", "en": "Opportunity brief"},
    "b.lead": {
        "zh": "下面是实测信号。请基于这些证据写 3 个具体的项目建议，不要泛泛而谈。",
        "en": "Measured signals below. Write 3 concrete project proposals from this evidence — no generic advice.",
    },
    "b.how": {"zh": "每个建议必须包含", "en": "Each proposal must contain"},
    "b.how_items": {
        "zh": "做给谁 · 解决什么 · 为什么是现在（引用下面的数字） · 最小可行版本是什么 · 最大的风险是什么",
        "en": "Who it is for · what it solves · why now (cite the numbers below) · smallest viable version · the biggest risk",
    },
    "b.footer": {"zh": "build-next · 每条数字都可复现，见 references/method.md", "en": "build-next · every number reproducible, see references/method.md"},
    "r.min": {"zh": "最低", "en": "min"},
    "r.median": {"zh": "中位", "en": "median"},
    "r.max": {"zh": "最高", "en": "max"},
    "r.bucket": {"zh": "分桶", "en": "bucket"},
}


def t(key: str, lang: str = "zh", **kw) -> str:
    e = MSG.get(key, {})
    s = e.get(lang) or e.get("en") or key
    return s.format(**kw) if kw else s
