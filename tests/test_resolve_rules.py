"""Tests for scripts/resolve-rules.py.

Covers:
- schema validation of rules.yaml
- idempotency on repeated runs
- BEGIN/END marker insertion when missing
- BEGIN/END marker replacement when already present
- legacy marker variants are recognised and replaced
- duplicate blocks collapse to one
- applies_to filter narrows the rule set correctly
- subscription directive overrides auto-detected tags
- --check mode exits non-zero when out of sync
- sync log appends a JSON line with stable schema
- audit line is appended to log.md when present
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

# Load resolve-rules.py as a module (the file uses a hyphen, so we go via spec).
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "resolve_rules", ROOT / "scripts" / "resolve-rules.py"
)
resolve_rules = importlib.util.module_from_spec(SPEC)
sys.modules["resolve_rules"] = resolve_rules
SPEC.loader.exec_module(resolve_rules)


@pytest.fixture
def sample_rules():
    """A minimal valid rules.yaml structure for unit tests."""
    return {
        "version": "1.0.0",
        "rules": [
            {
                "id": "r1",
                "title": "Always do A",
                "body": "Do A before B.",
                "applies_to": ["all"],
                "severity": "critical",
            },
            {
                "id": "r2",
                "title": "Card on board",
                "body": "Create a card.",
                "applies_to": ["has_board"],
                "severity": "important",
            },
            {
                "id": "r3",
                "title": "Service ports",
                "body": "Register ports.",
                "applies_to": ["runs_service"],
                "severity": "critical",
            },
        ],
        "closing_check": "Self-check before stopping.",
    }


@pytest.fixture
def rules_yaml_file(tmp_path, sample_rules, monkeypatch):
    path = tmp_path / "rules.yaml"
    path.write_text(yaml.safe_dump(sample_rules), encoding="utf-8")
    monkeypatch.setattr(resolve_rules, "RULES_PATH", path)
    monkeypatch.setattr(
        resolve_rules,
        "LOG_PATH",
        tmp_path / "sync-log.jsonl",
    )
    return path


@pytest.fixture
def claude_md_file(tmp_path):
    path = tmp_path / "CLAUDE.md"
    path.write_text(
        "# CLAUDE.md — sample\n\nProject-specific notes here.\n",
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def test_validate_passes_on_clean_rules(rules_yaml_file):
    assert resolve_rules.validate() == 0


def test_validate_fails_on_missing_field(tmp_path, monkeypatch):
    bad = {
        "version": "1.0.0",
        "rules": [{"id": "r1", "title": "x", "applies_to": ["all"], "severity": "critical"}],
    }
    path = tmp_path / "rules.yaml"
    path.write_text(yaml.safe_dump(bad), encoding="utf-8")
    monkeypatch.setattr(resolve_rules, "RULES_PATH", path)
    assert resolve_rules.validate() == 1


def test_validate_fails_on_duplicate_id(tmp_path, monkeypatch):
    bad = {
        "version": "1.0.0",
        "rules": [
            {"id": "r1", "title": "x", "body": "y", "applies_to": ["all"], "severity": "critical"},
            {"id": "r1", "title": "z", "body": "w", "applies_to": ["all"], "severity": "critical"},
        ],
    }
    path = tmp_path / "rules.yaml"
    path.write_text(yaml.safe_dump(bad), encoding="utf-8")
    monkeypatch.setattr(resolve_rules, "RULES_PATH", path)
    assert resolve_rules.validate() == 1


def test_validate_fails_on_bad_severity(tmp_path, monkeypatch):
    bad = {
        "version": "1.0.0",
        "rules": [
            {"id": "r1", "title": "x", "body": "y", "applies_to": ["all"], "severity": "WHATEVER"},
        ],
    }
    path = tmp_path / "rules.yaml"
    path.write_text(yaml.safe_dump(bad), encoding="utf-8")
    monkeypatch.setattr(resolve_rules, "RULES_PATH", path)
    assert resolve_rules.validate() == 1


def test_validate_fails_on_unknown_tag(tmp_path, monkeypatch):
    bad = {
        "version": "1.0.0",
        "rules": [
            {"id": "r1", "title": "x", "body": "y", "applies_to": ["BOGUS"], "severity": "critical"},
        ],
    }
    path = tmp_path / "rules.yaml"
    path.write_text(yaml.safe_dump(bad), encoding="utf-8")
    monkeypatch.setattr(resolve_rules, "RULES_PATH", path)
    assert resolve_rules.validate() == 1


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------


def test_filter_all_only(sample_rules):
    out = resolve_rules.filter_rules(sample_rules["rules"], {"all"})
    assert [r["id"] for r in out] == ["r1"]


def test_filter_with_board_includes_r2(sample_rules):
    out = resolve_rules.filter_rules(sample_rules["rules"], {"all", "has_board"})
    assert {r["id"] for r in out} == {"r1", "r2"}


def test_filter_full_tag_set(sample_rules):
    out = resolve_rules.filter_rules(
        sample_rules["rules"], {"all", "has_board", "runs_service"}
    )
    assert {r["id"] for r in out} == {"r1", "r2", "r3"}


def test_filter_skips_deprecated(sample_rules):
    sample_rules["rules"][0]["deprecated"] = True
    out = resolve_rules.filter_rules(sample_rules["rules"], {"all"})
    assert "r1" not in {r["id"] for r in out}


# ---------------------------------------------------------------------------
# Sync — insertion / replacement / idempotency
# ---------------------------------------------------------------------------


def test_inserts_block_when_absent(rules_yaml_file, claude_md_file):
    result = resolve_rules.sync_file(claude_md_file)
    assert "inserted" in result
    text = claude_md_file.read_text(encoding="utf-8")
    assert resolve_rules.BEGIN_MARKER in text
    assert resolve_rules.END_MARKER in text


def test_idempotent_after_first_run(rules_yaml_file, claude_md_file):
    resolve_rules.sync_file(claude_md_file)
    second = resolve_rules.sync_file(claude_md_file)
    assert "unchanged" in second
    third = resolve_rules.sync_file(claude_md_file)
    assert "unchanged" in third


def test_replaces_existing_block_in_place(rules_yaml_file, claude_md_file):
    resolve_rules.sync_file(claude_md_file)
    # Manually edit body inside markers — resolver must overwrite.
    text = claude_md_file.read_text(encoding="utf-8")
    text = text.replace("Do A before B.", "TAMPERED")
    claude_md_file.write_text(text, encoding="utf-8")
    result = resolve_rules.sync_file(claude_md_file)
    assert "updated" in result
    assert "TAMPERED" not in claude_md_file.read_text(encoding="utf-8")


def test_legacy_marker_variant_is_replaced(rules_yaml_file, claude_md_file):
    """Legacy markers from sync-operating-rules.py must be recognised."""
    legacy = (
        "# CLAUDE.md\n\n"
        "<!-- BEGIN INHERITED OPERATING RULES (auto-synced from ~/.claude/CLAUDE.md, do not edit by hand) -->\n"
        "OLD CONTENT\n"
        "<!-- END INHERITED OPERATING RULES -->\n\n"
        "Project notes.\n"
    )
    claude_md_file.write_text(legacy, encoding="utf-8")
    result = resolve_rules.sync_file(claude_md_file)
    assert "updated" in result
    final = claude_md_file.read_text(encoding="utf-8")
    assert final.count(resolve_rules.BEGIN_MARKER) == 1
    assert final.count(resolve_rules.END_MARKER) == 1
    assert "OLD CONTENT" not in final


def test_duplicate_blocks_collapse_to_one(rules_yaml_file, claude_md_file):
    """If two blocks exist (e.g. mid-migration), the resolver collapses them."""
    duplicated = (
        "# CLAUDE.md\n\n"
        f"{resolve_rules.BEGIN_MARKER}\n"
        "FIRST\n"
        f"{resolve_rules.END_MARKER}\n\n"
        f"{resolve_rules.BEGIN_MARKER}\n"
        "SECOND\n"
        f"{resolve_rules.END_MARKER}\n\n"
        "Project notes.\n"
    )
    claude_md_file.write_text(duplicated, encoding="utf-8")
    resolve_rules.sync_file(claude_md_file)
    final = claude_md_file.read_text(encoding="utf-8")
    assert final.count(resolve_rules.BEGIN_MARKER) == 1
    assert final.count(resolve_rules.END_MARKER) == 1


def test_subscription_directive_overrides_auto_tags(
    rules_yaml_file, claude_md_file
):
    """When a directive specifies applies_to, ignore detected tags."""
    text_with_directive = (
        "# CLAUDE.md\n\n"
        "<!-- include: claude-stack@v1 rules.yaml applies_to=runs_service -->\n\n"
        "Notes.\n"
    )
    claude_md_file.write_text(text_with_directive, encoding="utf-8")
    resolve_rules.sync_file(claude_md_file)
    body = claude_md_file.read_text(encoding="utf-8")
    # Directive said runs_service only — r1 (all) and r3 (runs_service) included,
    # r2 (has_board) excluded even though detect_tags would have added has_board
    # from cache.
    assert "Service ports" in body  # r3
    # r2 must not be present given strict directive
    assert "Card on board" not in body


def test_check_mode_returns_nonzero_when_out_of_sync(
    rules_yaml_file, claude_md_file
):
    # File starts without block — would change.
    result = resolve_rules.sync_file(claude_md_file, check=True)
    assert "OUT_OF_SYNC" in result
    # File still untouched (check mode is read-only).
    text = claude_md_file.read_text(encoding="utf-8")
    assert resolve_rules.BEGIN_MARKER not in text


def test_check_mode_returns_unchanged_when_in_sync(
    rules_yaml_file, claude_md_file
):
    resolve_rules.sync_file(claude_md_file)
    result = resolve_rules.sync_file(claude_md_file, check=True)
    assert "unchanged" in result


# ---------------------------------------------------------------------------
# Observability — sync log
# ---------------------------------------------------------------------------


def test_sync_log_contains_one_entry_per_run(
    rules_yaml_file, claude_md_file, tmp_path
):
    log_path = resolve_rules.LOG_PATH
    resolve_rules.sync_file(claude_md_file)
    resolve_rules.sync_file(claude_md_file)
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2
    for line in lines:
        entry = json.loads(line)
        for key in ("ts", "target", "action", "rule_ids", "rules_version"):
            assert key in entry


def test_audit_line_appended_to_log_md(
    rules_yaml_file, claude_md_file, tmp_path
):
    log_md = tmp_path / "log.md"
    log_md.write_text("# Project log\n\n", encoding="utf-8")
    resolve_rules.sync_file(claude_md_file)
    audit_text = log_md.read_text(encoding="utf-8")
    assert "rules synced @ claude-stack" in audit_text


def test_audit_line_skipped_when_log_md_missing(
    rules_yaml_file, claude_md_file
):
    # No log.md — should not error or create one.
    resolve_rules.sync_file(claude_md_file)
    assert not (claude_md_file.parent / "log.md").exists()
