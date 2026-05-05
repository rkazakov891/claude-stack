#!/usr/bin/env python3
"""Weekly summary of operating-rules sync activity.

Parses ~/.claude/cache/sync-log.jsonl, prints a summary suitable for posting
as a card body on the Roman PMO portfolio. Also flags projects whose CLAUDE.md
has not been synced in N days (default 14) — possible drift indicator.

Usage:
    sync-log-weekly-summary.py                   # last 7 days
    sync-log-weekly-summary.py --days 30         # last 30 days
    sync-log-weekly-summary.py --post            # also post a card via gh CLI
    sync-log-weekly-summary.py --stale-days 14   # threshold for "stale" warning
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "cache" / "sync-log.jsonl"


def load_entries() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    entries: list[dict] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def summarise(entries: list[dict], window_days: int, stale_days: int) -> str:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=window_days)
    in_window = [
        e for e in entries
        if datetime.fromisoformat(e["ts"]) >= window_start
    ]

    actions = Counter(e["action"] for e in in_window)
    targets = Counter(e["target"] for e in in_window)
    stack_shas = Counter(e["claude_stack_sha"] for e in in_window)

    last_sync_per_project: dict[str, datetime] = {}
    for entry in entries:
        ts = datetime.fromisoformat(entry["ts"])
        last_sync_per_project[entry["target"]] = max(
            last_sync_per_project.get(entry["target"], ts), ts
        )

    stale = [
        (target, ts)
        for target, ts in sorted(last_sync_per_project.items())
        if (now - ts).days > stale_days
    ]

    lines = [
        f"## Operating-rules sync — last {window_days} days",
        "",
        f"- **Total events:** {len(in_window)}",
        f"- **Actions:** "
        + ", ".join(f"`{action}`={count}" for action, count in actions.most_common())
        if actions
        else "- **Actions:** none",
        f"- **claude-stack SHAs touched:** "
        + ", ".join(f"`{sha}`={count}" for sha, count in stack_shas.most_common(5)),
        "",
        "### Per project",
    ]
    for target, count in sorted(targets.items()):
        last = last_sync_per_project.get(target)
        last_str = last.strftime("%Y-%m-%d %H:%M UTC") if last else "—"
        proj = Path(target).parent.name
        lines.append(f"- `{proj}` — {count} events, last sync `{last_str}`")

    if stale:
        lines.extend(["", f"### ⚠ Stale (> {stale_days} days since last sync)"])
        for target, ts in stale:
            proj = Path(target).parent.name
            age_days = (now - ts).days
            lines.append(f"- `{proj}` — {age_days} days ago")

    if not in_window and not stale:
        lines.append("")
        lines.append("_No sync activity this period._")

    return "\n".join(lines)


def post_card(body: str, project: str = "claude-stack") -> int:
    """Post the summary as a Roman PMO card via the helper lib."""
    import subprocess
    title = f"Sync log summary — week ending {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    helper = Path.home() / ".claude" / "scripts" / "lib" / "roman-pmo.sh"
    if not helper.exists():
        print(f"helper not found: {helper}", file=sys.stderr)
        return 1
    cmd = (
        f'source "{helper}" && '
        f'pmo_create_dual_task "{title}" "$1" "Project={project}" "Status=Done" "Type=chore"'
    )
    result = subprocess.run(
        ["bash", "-lc", cmd, "_", body],
        capture_output=True,
        text=True,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--stale-days", type=int, default=14)
    parser.add_argument("--post", action="store_true")
    args = parser.parse_args(argv[1:])

    entries = load_entries()
    summary = summarise(entries, args.days, args.stale_days)
    print(summary)

    if args.post:
        return post_card(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
