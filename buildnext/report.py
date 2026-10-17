"""Renderers: terminal table, markdown brief for an agent, and a dark HTML page."""
from __future__ import annotations

import html
import json
import unicodedata

from .i18n import t


def _pad(s: str, w: int) -> str:
    n = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)
    return s + " " * max(0, w - n)


def _reg_label(s: dict, lang: str) -> str:
    reg = s.get("registry") or {}
    if reg.get("has_match") is None:
        return t("t.unknown", lang)
    if reg.get("has_match"):
        return f"{t('t.has_hits', lang)} {reg.get('top_score')}"
    return t("t.vacant", lang)


def terminal(data: dict, lang: str = "zh") -> str:
    out = [f"\n  {t('t.title', lang)} · {data['since']}",
           f"  {t('t.scanned', lang, repos=data['repos_scanned'], topics=data['topics_scanned'])}\n",
           f"  {_pad(t('t.topic', lang), 28)}{t('t.score', lang):>8}{t('t.demand', lang):>8}"
           f"{t('t.repos', lang):>8}  {t('t.registry', lang)}"]
    for s in data["opportunities"]:
        out.append(
            f"  {_pad(s['topic'], 28)}{s['score']:>8}{s['best']:>8}"
            f"{(s.get('topic_repos') if s.get('topic_repos') is not None else '—'):>8}  "
            f"{_reg_label(s, lang)}   ← {s['repos'][0]}")
    if not data["opportunities"]:
        out.append(f"  {t('t.none', lang)}")
    out.append(f"\n  {t('t.caveat', lang)}\n")
    return "\n".join(out)


def markdown_brief(data: dict, lang: str = "zh") -> str:
    """Structured evidence an agent can read and turn into proposals."""
    L = [f"# {t('b.title', lang)} — {data['since']}", "",
         f"{t('b.lead', lang)}", "",
         f"**{t('b.how', lang)}**：{t('b.how_items', lang)}", "",
         f"_{t('t.scanned', lang, repos=data['repos_scanned'], topics=data['topics_scanned'])}_",
         "", f"## {t('t.opps', lang)}", ""]
    for i, s in enumerate(data["opportunities"], 1):
        reg = s.get("registry") or {}
        L += [f"### {i}. `{s['topic']}` — {s['score']}/100", "",
              f"- {t('t.demand', lang)}: **{s['best']}** "
              f"({t('t.trigger', lang)} `{s['repos'][0]}`, {s['best_stars']} stars, "
              f"{t('t.buckets', lang)} {', '.join(s['best_buckets'])})",
              f"- {t('t.repos', lang)}: **{s.get('topic_repos')}** "
              f"(supply percentile {s['supply_percentile']})",
              f"- {t('t.registry', lang)}: {_reg_label(s, lang)}"
              + (f" — `{reg.get('top_slug')}`" if reg.get("top_slug") else ""),
              f"- triggers: {', '.join('`' + r + '`' for r in s['repos'][:4])}", ""]
    L += ["---", "", f"_{t('t.caveat', lang)}_"]
    return "\n".join(L)


def html_report(data: dict, lang: str = "zh", alt_href: str | None = None,
                alt_label: str | None = None) -> str:
    sw = (f'<a class="lang" href="{html.escape(alt_href)}">{html.escape(alt_label)}</a>'
          if alt_href and alt_label else "")

    rows = []
    for i, s in enumerate(data["opportunities"], 1):
        reg = s.get("registry") or {}
        vacant = reg.get("has_match") is False
        badge = (f'<span class="bd v">{t("t.vacant", lang)}</span>' if vacant
                 else f'<span class="bd">{_reg_label(s, lang)}</span>')
        rows.append(f"""<div class="card">
  <div class="ch"><span class="rk">{i}</span><code class="tp">{html.escape(s['topic'])}</code>
    <span class="sc">{s['score']:g}</span></div>
  <div class="meta">
    <span>{t('t.demand', lang)} <b>{s['best']}</b></span>
    <span>{t('t.repos', lang)} <b>{s.get('topic_repos')}</b></span>
    {badge}
  </div>
  <div class="trig">← {html.escape(s['repos'][0])} · {s['best_stars']} stars · {html.escape(', '.join(s['best_buckets']))}</div>
  <div class="bar"><i style="width:{min(100, s['score'])}%"></i></div>
</div>""")

    fl = data.get("floors") or {}
    ftable = "".join(
        f"<tr><td>{html.escape(str(b))}</td><td>{v.get('min')}</td><td>{v.get('median')}</td>"
        f"<td>{v.get('max')}</td></tr>" for b, v in fl.items()
    )

    return f"""<!DOCTYPE html><html lang="{'zh-CN' if lang == 'zh' else 'en'}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t('t.title', lang)} · build-next</title>
<style>
:root{{--bg:#16171a;--panel:#1e1f24;--line:#33353c;--tx:#e8e6e2;--tx2:#a8a7a3;--amber:#ef9f27;--teal:#5dcaa5;--red:#e26d6b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:14px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}
.wrap{{max-width:860px;margin:0 auto;padding:40px 22px 70px;position:relative}}
.lang{{position:absolute;top:42px;right:22px;font-size:12.5px;color:var(--tx2);text-decoration:none;border:0.5px solid var(--line);border-radius:99px;padding:3px 12px}}
h1{{font-size:20px;font-weight:600;margin:0 0 4px}}
.sub{{color:var(--tx2);margin:0 0 6px;font-size:13px}}
.stats{{color:#7a7975;font-size:12.5px;margin:0 0 26px}}
h2{{font-size:14px;font-weight:600;color:var(--tx2);margin:32px 0 12px}}
code{{background:#25272d;padding:1px 5px;border-radius:4px;font-size:12.5px}}
.card{{background:var(--panel);border:0.5px solid var(--line);border-radius:10px;padding:13px 16px;margin-bottom:9px}}
.ch{{display:flex;align-items:center;gap:10px;margin-bottom:7px}}
.rk{{width:19px;height:19px;border-radius:50%;background:#25272d;color:var(--tx2);font-size:11px;display:flex;align-items:center;justify-content:center;flex:0 0 auto}}
.tp{{font-size:13.5px;font-weight:500}}
.sc{{margin-left:auto;color:var(--amber);font-size:19px;font-weight:600;line-height:1}}
.meta{{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:var(--tx2);margin-bottom:5px}}
.meta b{{color:var(--tx);font-weight:500}}
.bd{{font-size:11.5px;border:0.5px solid var(--line);border-radius:99px;padding:1px 9px;color:var(--tx2)}}
.bd.v{{color:var(--teal);border-color:#2f6f58}}
.trig{{font-size:12px;color:#7a7975}}
.bar{{height:3px;background:#25272d;border-radius:99px;margin-top:9px;overflow:hidden}}
.bar i{{display:block;height:100%;background:var(--amber);border-radius:99px}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:4px}}
th,td{{text-align:left;padding:6px 10px;border-bottom:0.5px solid var(--line)}}
th{{color:var(--tx2);font-weight:500;font-size:12px}}
.caveat{{margin-top:26px;padding:12px 16px;border-left:2px solid var(--red);background:#1f1a1a;color:#d8b6b4;font-size:12.5px;border-radius:0 8px 8px 0}}
footer{{margin-top:36px;color:#7a7975;font-size:12px}}
</style></head><body><div class="wrap">
{sw}
<h1>{t('t.title', lang)}</h1>
<p class="sub">{t('t.sub', lang)}</p>
<p class="stats">{t('t.scanned', lang, repos=data['repos_scanned'], topics=data['topics_scanned'])} · since={data['since']}</p>
<h2>{t('t.opps', lang)}</h2>
{''.join(rows) or f'<p class="sub">{t("t.none", lang)}</p>'}
<h2>{t('t.floors', lang)}</h2>
<table><thead><tr><th>{t('r.bucket', lang)}</th><th>{t('r.min', lang)}</th><th>{t('r.median', lang)}</th><th>{t('r.max', lang)}</th></tr></thead>
<tbody>{ftable}</tbody></table>
<div class="caveat">{t('t.caveat', lang)}</div>
<footer>{t('b.footer', lang)}</footer>
</div></body></html>"""


def to_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
