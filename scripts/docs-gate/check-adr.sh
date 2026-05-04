#!/usr/bin/env bash
# Проверка наличия ADR для архитектурных изменений
# Exit 0 — PASS, exit 1 — FAIL (нужен ADR)
# Аргументы: [base-branch] (default: main)

set -e

BASE="${1:-main}"

# Признаки архитектурного изменения (heuristics):
# 1. Новые файлы в src/, lib/, app/
# 2. Изменение публичных интерфейсов (def public_*, export class и т.п.)
# 3. Новые модули верхнего уровня

NEW_FILES=$(git diff --name-status "origin/$BASE...HEAD" 2>/dev/null | grep -E '^A\s+(src|lib|app|core)/' | awk '{print $2}' || true)
PUBLIC_API_CHANGES=$(git diff "origin/$BASE...HEAD" -- '*.py' '*.ts' '*.go' 2>/dev/null | grep -cE '^\+\s*(def|class|export|func)\s' || true)
NEW_ADRS=$(git diff --name-only "origin/$BASE...HEAD" 2>/dev/null | grep -E '^(docs/decisions|decisions)/.+\.md$' || true)

ARCHITECTURAL=0
[[ -n "$NEW_FILES" ]] && ARCHITECTURAL=1
[[ "$PUBLIC_API_CHANGES" -gt 5 ]] && ARCHITECTURAL=1

if [[ $ARCHITECTURAL -eq 1 && -z "$NEW_ADRS" ]]; then
  echo "❌ FAIL: архитектурные изменения требуют ADR"
  echo ""
  [[ -n "$NEW_FILES" ]] && echo "Новые модули:" && echo "$NEW_FILES"
  [[ "$PUBLIC_API_CHANGES" -gt 5 ]] && echo "Изменений публичного API: $PUBLIC_API_CHANGES (порог 5)"
  echo ""
  echo "Создайте ADR через: /document decision <slug>"
  exit 1
fi

if [[ -n "$NEW_ADRS" ]]; then
  echo "✅ PASS: ADR найден ($NEW_ADRS)"
else
  echo "✅ PASS: тривиальные изменения, ADR не нужен"
fi
