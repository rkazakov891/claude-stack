# ADR: Rules-as-data + subscribe pattern (A++ inheritance system)

- **Date:** 2026-05-05
- **Status:** accepted
- **Layer:** claude-stack architecture; Claude Code harness integration
- **Affects:** `claude-stack/rules.yaml` (new), `claude-stack/scripts/resolve-rules.py` (new), `claude-stack/tests/` (new), `~/.claude/CLAUDE.md` (becomes a thin pointer), per-project `CLAUDE.md` (subscription line replaces replicated block), `~/.claude/hooks/sync-operating-rules-hook.sh` (replaced by resolver hook), `~/.claude/skills/rules/` (new `/rules` skill).

## Context

The earlier inheritance system (ADR-less, shipped same day in this session) propagates the «🔴 ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА» section from `~/.claude/CLAUDE.md` into every per-project `CLAUDE.md` between `BEGIN/END INHERITED OPERATING RULES` markers. It works, but has known weaknesses:

1. **Replicated copies.** The same text exists in 5+ files; the marker block is fragile to manual editing.
2. **No schema.** Rules are bullet points in markdown — adding a `applies_to` filter, a `severity`, or a stable `id` requires regex archaeology.
3. **No tests.** Idempotency was verified by hand; the next refactor of the global file's headings could silently break the regex extraction.
4. **No audit trail.** When the global file changes, all per-project copies update immediately; we can no longer reproduce «what rules were active when ADR X was written».
5. **No observability.** A failed sync only surfaces if Claude Code reports a hook error; otherwise the per-project file goes stale silently.
6. **No introspection.** There is no command to ask «what rules are active in this project?», or to diff against the source.

The goal of this ADR is to capture the next-step architecture that turns the inheritance system from a personal hack (B+) into a small but rigorous component of claude-stack (A++).

## Decision

Move from **markdown text replication** to **rules-as-data + subscribe pattern**:

1. **Source of truth:** a structured `claude-stack/rules.yaml` file with one entry per rule, each carrying:
   - `id` — stable identifier (`r1` … `rN`)
   - `title` — short human-readable title
   - `body` — the rule text (multi-line, markdown allowed)
   - `applies_to` — list of tags (`all`, `has_board`, `has_repo`, `runs_service`, …); the resolver filters by these
   - `severity` — `critical` / `important` / `nice-to-have`
   - `version` — semver, bumped per change (additive change = minor, semantics change = major)
   - `examples_pass` / `examples_fail` (optional) — short illustrations for prompt clarity

2. **Resolver:** `claude-stack/scripts/resolve-rules.py` reads `rules.yaml` plus a target file's subscription directive, applies any `applies_to` filter and version pin, and emits the marker block content. Replaces the previous regex-based `sync-operating-rules.py`.

3. **Subscription directive in per-project `CLAUDE.md`:** instead of a replicated block, every project carries a single line like:

   ```html
   <!-- include: claude-stack@v1 rules.yaml applies_to=has_board,has_repo -->
   ```

   The resolver expands this at sync time. The expanded block stays between the same `BEGIN/END INHERITED OPERATING RULES` markers, so existing per-project files migrate cleanly.

4. **Tests + CI gate:** `claude-stack/tests/test_resolve_rules.py` covers schema validation, idempotency, marker insertion edge cases, applies_to filtering, version pinning, broken YAML, Unicode. GitHub Actions runs them on every push to claude-stack.

5. **Observability:** the resolver writes a JSON-lines log entry per sync (`~/.claude/cache/sync-log.jsonl`), capturing source hash, target file, action, before/after hashes, applied rule IDs. A weekly summary script posts a card on Roman PMO portfolio with sync health.

6. **`/rules` slash command:** new skill at `~/.claude/skills/rules/SKILL.md` with subcommands `list`, `check`, `diff`, `pin`. Lets the operator inspect / verify / freeze the rules in any project.

7. **Audit trail:** when the resolver updates a project's block, it appends a one-line marker to `<project>/log.md` with claude-stack git SHA and active rule IDs. Future ADRs can reference «rules @<sha>» for reproducibility.

## Alternatives considered

### Status quo (B+) — keep marker-based markdown replication

- Pros: zero migration cost, already works.
- Cons: every weakness above remains. Will not survive the next non-trivial schema change (e.g. adding `applies_to`).

### Patch the existing system — just add tests + structured logging

- Pros: smallest delta from current state.
- Cons: still no `applies_to`, no audit trail of historical versions, no introspection. Lipstick on the regex-based design.

### Migrate to dotbot / chezmoi / yadm

- Pros: proven dotfile-management tools with templating, conditional inclusion, multi-machine sync.
- Cons: introduces a heavyweight third-party dependency for a system that conceptually fits in 200 lines of Python; learning-curve cost; couples the rules-system to an external project's release cadence.

### LLM-judge for rule adherence (skip for now)

- Pros: would surface «Claude broke rule #6 in session X» as a metric.
- Cons: requires hundreds of sessions per week to be useful; premature for a solo developer with ~10 sessions/day.

### Cryptographically signed `rules.yaml`

- Pros: tamper-evident audit trail.
- Cons: solo developer, single trusted source. Ceremony without real risk reduction.

## Consequences

### Positive

- **Single source of truth.** `rules.yaml` in claude-stack. All other CLAUDE.md files just point at it.
- **Schema evolution.** Adding fields (e.g. `applies_to`, `examples_pass`) is non-breaking and backwards-compatible.
- **Audit trail.** Git history of `rules.yaml` plus `log.md` markers in each project = full reproducibility.
- **Observability.** Structured sync log surfaces failures and drift without manual checking.
- **Introspection via `/rules`.** Operator can answer «what is active here?» and «what changed since yesterday?» in one command.
- **Multi-machine consistency.** `rules.yaml` lives in claude-stack (cloud-versioned); any machine that pulls it gets the same rules.
- **Selective application.** `applies_to` lets us tag rules as e.g. `has_board` so projects in «чулане» (no board) do not get rule #6 noise.

### Negative

- **Migration cost.** ~12 hours total across the 8 follow-up tasks; existing 5 projects need their CLAUDE.md edited.
- **Dependence on YAML library.** New runtime dep (`PyYAML`, already in most Python installations but worth noting).
- **Per-project `CLAUDE.md` becomes opaque to readers.** A subscription line gives no information about what rules apply; readers must run `/rules list` or open `rules.yaml`. Mitigation: the resolver still expands the block between markers, so the rendered markdown is identical to today — only the *source* of the text becomes a directive.
- **One more script in claude-stack to maintain.** Offset by deletion of `~/.claude/scripts/sync-operating-rules.py`.

### Neutral

- The marker block (`BEGIN/END INHERITED OPERATING RULES`) stays — only its contents become resolver-generated. This means existing tooling that reads the markers continues to work unchanged.

## Validation

The migration is considered successful when:

1. `pytest claude-stack/tests/` passes locally and in GitHub Actions.
2. `python scripts/resolve-rules.py --all` produces byte-identical output for the 5 existing projects after migration.
3. `/rules list` returns the 8 current rules with version `v1.0.0` for any project.
4. `/rules diff` returns empty diff right after migration.
5. A test edit to `rules.yaml` (add a 9th rule, push) propagates to all 5 projects on the next session start.
6. The weekly sync summary card lands on Roman PMO portfolio.

## Revisit when

- Number of rules crosses ~20 — at that point we may need rule categories / a UI rendering layer.
- Adoption beyond solo developer (team or shared org rules) — would need cryptographic signing and review workflow.
- Cross-platform sync needed — would replace local sync log with a shared store.
