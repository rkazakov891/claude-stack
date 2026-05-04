#!/usr/bin/env bash
# Запуск всех docs-gate проверок последовательно
# Exit 0 — все PASS, exit 1 — есть FAIL
# Аргументы: [base-branch] [docstring-threshold]

set +e  # не выходим после первой ошибки — собираем все

BASE="${1:-main}"
THRESHOLD="${2:-70}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

FAILED=0
RESULTS=""

run_check() {
  local name="$1"
  local script="$2"
  shift 2

  echo ""
  echo "════════════════════════════════════════"
  echo "  Check: $name"
  echo "════════════════════════════════════════"
  if bash "$SCRIPT_DIR/$script" "$@"; then
    RESULTS+="  ✅ $name\n"
  else
    RESULTS+="  ❌ $name\n"
    FAILED=1
  fi
}

run_check "ADR для архитектурных изменений" "check-adr.sh" "$BASE"
run_check "Docstring coverage" "check-docstrings.sh" "$THRESHOLD"
run_check "CHANGELOG обновлён" "check-changelog.sh" "$BASE"

echo ""
echo "════════════════════════════════════════"
echo "  Docs Gate Summary"
echo "════════════════════════════════════════"
echo -e "$RESULTS"

if [[ $FAILED -eq 1 ]]; then
  echo "❌ Docs Gate: FAIL"
  echo ""
  echo "Опции:"
  echo "  • Исправить вручную (написать ADR / docstrings / changelog entry)"
  echo "  • Запустить AI fallback: bash scripts/docs-gate/ai-fallback.sh"
  exit 1
fi

echo "✅ Docs Gate: PASS"
