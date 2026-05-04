#!/usr/bin/env bash
# Проверка обновления CHANGELOG.md в текущем PR
# Exit 0 — PASS, exit 1 — FAIL (changelog не обновлён)
# Аргументы: [base-branch] (default: main)

set -e

BASE="${1:-main}"

# Игнорируем чисто docs/test/ci-only PR
SOURCE_CHANGED=$(git diff --name-only "origin/$BASE...HEAD" 2>/dev/null | grep -vE '^(docs/|tests?/|\.github/|\.|\*\.md$)' | head -5 || true)

if [[ -z "$SOURCE_CHANGED" ]]; then
  echo "✅ PASS: только docs/tests/ci изменения, changelog не обязателен"
  exit 0
fi

# Проверяем что хоть один changelog был изменён
CHANGELOG_CHANGED=$(git diff --name-only "origin/$BASE...HEAD" 2>/dev/null | grep -E '(CHANGELOG\.md|docs/changelog\.md)' || true)

if [[ -z "$CHANGELOG_CHANGED" ]]; then
  echo "❌ FAIL: CHANGELOG не обновлён"
  echo ""
  echo "Изменены source-файлы:"
  echo "$SOURCE_CHANGED"
  echo ""
  echo "Добавьте запись в секцию [Unreleased] в CHANGELOG.md или docs/changelog.md"
  exit 1
fi

echo "✅ PASS: CHANGELOG обновлён ($CHANGELOG_CHANGED)"
