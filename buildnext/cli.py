"""CLI: `buildnext scan`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import gaps, report


def cmd_scan(a) -> int:
    data = gaps.scan(limit_per_bucket=a.limit, max_topics=a.max_topics,
                     check_registry=not a.no_registry, since=a.since)

    if a.json:
        print(report.to_json(data))
    else:
        print(report.terminal(data, a.lang))

    if a.md:
        Path(a.md).write_text(report.markdown_brief(data, a.lang), encoding="utf-8")
        print(f"  brief    -> {a.md}")

    if a.html:
        other = "en" if a.lang == "zh" else "zh"
        Path(a.html).write_text(
            report.html_report(data, lang=a.lang, alt_href=a.alt_href,
                               alt_label=a.alt_label or ("English" if other == "en" else "中文")),
            encoding="utf-8")
        print(f"  html     -> {a.html}")

    if a.site:
        d = Path(a.site)
        d.mkdir(parents=True, exist_ok=True)
        other_lang = "en" if a.lang == "zh" else "zh"
        pair = {a.lang: data, other_lang: data}  # same evidence, two languages
        zh, en = pair.get("zh"), pair.get("en")
        (d / "index.html").write_text(
            report.html_report(zh, lang="zh", alt_href="en.html", alt_label="English"), encoding="utf-8")
        (d / "en.html").write_text(
            report.html_report(en, lang="en", alt_href="index.html", alt_label="中文"), encoding="utf-8")
        (d / "brief.md").write_text(report.markdown_brief(data, "zh"), encoding="utf-8")
        print(f"  site     -> {d}/index.html (zh) + {d}/en.html (en) + brief.md")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="buildnext", description="What to build next, measured.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="demand minus supply, ranked")
    s.add_argument("--since", default="daily", choices=["daily", "weekly", "monthly"])
    s.add_argument("--limit", type=int, default=12, help="trending repos per bucket to deep-scan")
    s.add_argument("--max-topics", type=int, default=18, help="cap on topic lookups (search quota)")
    s.add_argument("--no-registry", action="store_true", help="skip the skill-registry probe")
    s.add_argument("--lang", default="zh", choices=["zh", "en"])
    s.add_argument("--json", action="store_true")
    s.add_argument("--md", help="write an agent-ready markdown brief here")
    s.add_argument("--html", help="write a dark HTML page here")
    s.add_argument("--alt-href", help="with --html: link to the other-language page")
    s.add_argument("--alt-label", help="with --html: label for that link")
    s.add_argument("--site", help="write both languages into this directory")
    s.set_defaults(func=cmd_scan)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except RuntimeError as e:
        print(f"  error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
