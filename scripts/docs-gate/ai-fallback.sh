#!/usr/bin/env bash
# AI fallback: запускает Claude (через Claude Code или Claude API) для генерации
# недостающей документации после провала docs-gate.
#
# Локально: использует Claude Code session (если запущена)
# В CI: использует ANTHROPIC_API_KEY + curl к API
#
# Использование (локально из ship-gate):
#   bash ai-fallback.sh local <base-branch>
# Использование (в CI):
#   bash ai-fallback.sh ci <base-branch>

set -e

MODE="${1:-local}"
BASE="${2:-main}"

if [[ "$MODE" == "local" ]]; then
  echo "==> AI fallback (local mode)"
  echo ""
  echo "В контексте Claude Code session попроси:"
  echo ""
  echo "  Запустить docs-gate, проанализировать FAIL'ы, и:"
  echo "  1. Для каждого недостающего ADR — создать черновик через /document decision"
  echo "  2. Для public функций без docstrings — добавить шаблонные docstrings"
  echo "  3. Для пустого CHANGELOG — выписать изменения из git diff в Unreleased"
  echo ""
  echo "Команда: запустить /tasks работу над docs-gate fail'ами"
  exit 0
fi

# CI mode — прямой вызов Claude API
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "❌ ANTHROPIC_API_KEY не задан — пропускаем AI fallback"
  exit 1
fi

echo "==> AI fallback (CI mode) — TODO: implementation via Claude API"
echo "Это будет реализовано когда добавим anthropics/claude-code-action в workflow."
echo "Пока — просто провал gate, разработчик пишет вручную."
exit 1
