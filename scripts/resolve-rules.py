#!/usr/bin/env python3
"""Resolve operating-rules subscriptions in per-project CLAUDE.md files.

Reads `claude-stack/rules.yaml` and renders the rules into a marker-bounded
block of every target file. Replaces the regex-based sync-operating-rules.py.

The target file may carry an explicit subscription directive:

    <!-- include: claude-stack@v1 rules.yaml applies_to=has_board,has_repo -->

If absent, the resolver auto-detects the project's tags and applies the full
rules.yaml. The block stays between BEGIN/END INHERITED OPERATING RULES so
existing tooling continues to work.

Usage:
    resolve-rules.py <path/to/CLAUDE.md>     # sync one file
    resolve-rules.py --all                   # sweep G:/Projects/*/CLAUDE.md
    resolve-rules.py --validate              # schema check, no writes
    resolve-rules.py --check <path>          # exit 1 if file would change

Logs every action as a JSON line in ~/.claude/cache/sync-log.jsonl for
observability and weekly summaries.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# The script lives at <repo>/scripts/resolve-rules.py — derive the repo root
# from the file location so it works regardless of where the repo was checked
# out (local cache, GitHub Actions runner, etc.).
CLAUDE_STACK_ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = CLAUDE_STACK_ROOT / "rules.yaml"
PROJECTS_ROOT = Path("G:/Projects") if Path("G:/Projects").exists() else Path("/g/Projects")

# Canonical marker text used when writing. Short and stable so future
# changes to the preamble do not break round-trips.
BEGIN_MARKER = "<!-- BEGIN INHERITED OPERATING RULES -->"
END_MARKER = "<!-- END INHERITED OPERATING RULES -->"

# Pattern for finding any existing block — matches the canonical short form
# AND the legacy variants that include source-description text in parens
# (the previous sync-operating-rules.py marker, and the brief earlier variant
# of this resolver). Migration from any of them is automatic.
BEGIN_MATCH_RE = re.compile(
    r"<!--\s*BEGIN INHERITED OPERATING RULES(?:\s*\([^)]*\))?\s*-->",
    re.IGNORECASE,
)

INCLUDE_RE = re.compile(
    r"<!--\s*include:\s*claude-stack(?:@(?P<pin>[^\s]+))?\s+rules\.yaml"
    r"(?:\s+applies_to=(?P<applies>[^\s]+))?"
    r"(?:\s+version=(?P<ver>[^\s]+))?\s*-->"
)

LOG_PATH = Path.home() / ".claude" / "cache" / "sync-log.jsonl"


# ---------------------------------------------------------------------------
# Loading + filtering
# ---------------------------------------------------------------------------


def load_rules(path: Path | None = None) -> dict:
    """Load rules.yaml; raise on schema problems caught early.

    Resolves the path at call time (not import time) so tests can monkeypatch
    ``RULES_PATH`` on the module and have it take effect here.
    """
    if path is None:
        path = RULES_PATH
    if not path.exists():
        raise FileNotFoundError(f"rules.yaml not found at {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "rules" not in data or "version" not in data:
        raise ValueError("rules.yaml must have top-level 'version' and 'rules'")
    return data


def filter_rules(rules: list[dict], tags: set[str]) -> list[dict]:
    """Return rules whose applies_to includes 'all' or any tag in `tags`."""
    out: list[dict] = []
    for rule in rules:
        if rule.get("deprecated"):
            continue
        applies = set(rule.get("applies_to", []))
        if "all" in applies or applies & tags:
            out.append(rule)
    return out


def detect_tags(target_path: Path) -> set[str]:
    """Infer applies_to tags from project state on disk."""
    project_root = target_path.parent
    tags: set[str] = {"all"}

    if (project_root / ".git").exists() or (project_root / ".github").exists():
        tags.add("has_repo")
    if (project_root / "decisions").is_dir():
        tags.add("has_decisions")
    if (project_root / "memory" / "ports.md").exists():
        tags.add("runs_service")

    cache = Path.home() / ".claude" / "cache" / "per-project-numbers.json"
    if cache.exists():
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
            if project_root.name in data:
                tags.add("has_board")
        except json.JSONDecodeError:
            pass

    return tags


def parse_directive(text: str) -> dict | None:
    """Extract subscription directive from the file. None if absent."""
    match = INCLUDE_RE.search(text)
    if not match:
        return None
    return match.groupdict()


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_rules(data: dict, rules: list[dict], applied_tags: set[str]) -> str:
    """Produce the rendered markdown body that goes between markers."""
    lines: list[str] = [
        "## 🔴 ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА (нарушение = баг моего поведения)",
        "",
        f"Эти {len(rules)} правил соблюдаются **всегда** для этого проекта. "
        f"Если я их нарушаю — Роман прав указывать мне на это.",
        "",
        f"_Source: `claude-stack/rules.yaml` v{data['version']} · "
        f"applied tags: `{', '.join(sorted(applied_tags))}`_",
        "",
    ]
    for i, rule in enumerate(rules, 1):
        lines.append(f"### {i}. {rule['title']} (`{rule['id']}`)")
        lines.append("")
        body = rule["body"].rstrip()
        for body_line in body.splitlines():
            lines.append(body_line)
        lines.append("")
    if "closing_check" in data:
        lines.append("---")
        lines.append("")
        lines.append(data["closing_check"].strip())
    return "\n".join(lines).rstrip() + "\n"


def get_claude_stack_sha() -> str:
    """Return short SHA of the claude-stack HEAD; 'unknown' on any failure."""
    try:
        return subprocess.check_output(
            ["git", "-C", str(CLAUDE_STACK_ROOT), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def build_block(data: dict, rules: list[dict], tags: set[str], sha: str) -> str:
    """Wrap rendered rules between markers with a preamble."""
    rendered = render_rules(data, rules, tags)
    preamble = (
        f"> 🔴 **Inherited operating rules** from `claude-stack/rules.yaml` "
        f"(v{data['version']} @ git `{sha}`).\n"
        "> Do not edit between the markers — overwritten on next sync.\n"
        "> Refresh: `python ~/.claude/cache/claude-stack/scripts/resolve-rules.py <this file>` "
        "or `--all`. PostToolUse hook keeps it fresh on every `rules.yaml` edit.\n"
    )
    return f"{BEGIN_MARKER}\n\n{preamble}\n{rendered}\n{END_MARKER}"


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


def hash_str(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def log_event(
    target: Path,
    action: str,
    before_hash: str,
    after_hash: str,
    sha: str,
    rule_ids: list[str],
    rules_version: str,
) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": str(target),
        "action": action,
        "before_hash": before_hash,
        "after_hash": after_hash,
        "claude_stack_sha": sha,
        "rules_version": rules_version,
        "rule_ids": rule_ids,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def append_audit_to_log_md(project_root: Path, sha: str, rules_version: str, rule_ids: list[str]) -> None:
    """Append a one-line audit marker to <project>/log.md (if it exists)."""
    log_md = project_root / "log.md"
    if not log_md.exists():
        return
    line = (
        f"\n- {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} — "
        f"rules synced @ claude-stack `{sha}`, v{rules_version}, "
        f"active: {', '.join(rule_ids)}\n"
    )
    with log_md.open("a", encoding="utf-8") as fh:
        fh.write(line)


def sync_file(target: Path, *, check: bool = False, audit: bool = True) -> str:
    """Sync one target file. Returns a status string."""
    if not target.exists():
        return f"skip (missing): {target}"

    text = target.read_text(encoding="utf-8")
    data = load_rules()

    directive = parse_directive(text)
    if directive and directive.get("applies"):
        tags = set(directive["applies"].split(","))
    else:
        tags = detect_tags(target)

    rules = filter_rules(data["rules"], tags)
    sha = get_claude_stack_sha()
    new_block = build_block(data, rules, tags, sha)
    before_hash = hash_str(text)

    block_pattern = re.compile(
        BEGIN_MATCH_RE.pattern + r".*?" + re.escape(END_MARKER),
        flags=re.DOTALL | re.IGNORECASE,
    )

    if block_pattern.search(text):
        # Replace ALL existing blocks (handles previously-duplicated state from
        # earlier marker-text drift). After this pass the file has exactly one.
        new_text, _ = block_pattern.subn(new_block, text)
        # If multiple blocks existed, re-collapse: keep only the first.
        first = new_text.find(BEGIN_MARKER)
        if first != -1:
            second = new_text.find(BEGIN_MARKER, first + len(BEGIN_MARKER))
            if second != -1:
                # Drop everything from the duplicate's BEGIN through its END.
                end_of_duplicate = new_text.find(END_MARKER, second)
                if end_of_duplicate != -1:
                    end_of_duplicate += len(END_MARKER)
                    new_text = new_text[:second] + new_text[end_of_duplicate:]
        action = "updated"
    else:
        lines = text.splitlines(keepends=True)
        h1_idx = next(
            (i for i, line in enumerate(lines) if line.lstrip().startswith("# ")),
            None,
        )
        if h1_idx is not None:
            insert_at = h1_idx + 1
            if insert_at < len(lines) and lines[insert_at].strip() == "":
                insert_at += 1
            new_lines = lines[:insert_at] + [f"\n{new_block}\n\n"] + lines[insert_at:]
        else:
            new_lines = [f"{new_block}\n\n", *lines]
        new_text = "".join(new_lines)
        action = "inserted"

    after_hash = hash_str(new_text)
    if new_text == text:
        action = "unchanged"

    if check:
        return f"{action}: {target}" if action == "unchanged" else f"OUT_OF_SYNC: {target}"

    if action != "unchanged":
        target.write_text(new_text, encoding="utf-8")

    rule_ids = [r["id"] for r in rules]
    log_event(target, action, before_hash, after_hash, sha, rule_ids, data["version"])
    if audit and action != "unchanged":
        append_audit_to_log_md(target.parent, sha, data["version"], rule_ids)

    return f"{action}: {target}"


def find_all_targets() -> list[Path]:
    if not PROJECTS_ROOT.exists():
        return []
    return sorted(p for p in PROJECTS_ROOT.glob("*/CLAUDE.md") if p.is_file())


def validate() -> int:
    data = load_rules()
    issues: list[str] = []
    seen_ids: set[str] = set()
    for rule in data["rules"]:
        for required in ("id", "title", "body", "applies_to", "severity"):
            if required not in rule:
                issues.append(f"rule missing '{required}': {rule.get('id', '?')}")
        rid = rule.get("id")
        if rid in seen_ids:
            issues.append(f"duplicate id: {rid}")
        if rid:
            seen_ids.add(rid)
        sev = rule.get("severity")
        if sev not in {"critical", "important", "nice-to-have"}:
            issues.append(f"rule {rid}: bad severity '{sev}'")
        for tag in rule.get("applies_to", []):
            if tag not in {"all", "has_board", "has_repo", "has_decisions", "runs_service"}:
                issues.append(f"rule {rid}: unknown applies_to tag '{tag}'")
    if issues:
        for issue in issues:
            print(f"FAIL  {issue}", file=sys.stderr)
        return 1
    print(f"OK    rules.yaml v{data['version']} — {len(data['rules'])} rules, schema valid")
    return 0


def main(argv: list[str]) -> int:
    args = argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2

    if args[0] == "--validate":
        return validate()

    check = "--check" in args
    args = [a for a in args if a != "--check"]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2

    if args[0] == "--all":
        targets = find_all_targets()
        if not targets:
            print(f"no per-project CLAUDE.md found under {PROJECTS_ROOT}", file=sys.stderr)
            return 0
        any_oos = False
        for target in targets:
            result = sync_file(target, check=check)
            print(result)
            if "OUT_OF_SYNC" in result:
                any_oos = True
        return 1 if (check and any_oos) else 0

    target = Path(args[0])
    result = sync_file(target, check=check)
    print(result)
    return 1 if (check and "OUT_OF_SYNC" in result) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
