#!/usr/bin/env bash
# Проверка docstring coverage для изменённых файлов
# Exit 0 — PASS, exit 1 — FAIL (есть public API без docstring)
# Аргументы: [threshold] (default: 70)

set -e

THRESHOLD="${1:-70}"

# Python — interrogate
if find . -name "*.py" -not -path "*/\.*" -not -path "*/node_modules/*" -not -path "*/site/*" 2>/dev/null | head -1 | grep -q .; then
  if ! command -v interrogate >/dev/null 2>&1; then
    echo "Устанавливаю interrogate..."
    pip install -q interrogate
  fi

  echo "==> Python docstring coverage (threshold: ${THRESHOLD}%)"
  if interrogate --fail-under="$THRESHOLD" --quiet 2>/dev/null; then
    echo "✅ PASS: Python docstring coverage ≥ ${THRESHOLD}%"
  else
    echo "❌ FAIL: Python docstring coverage ниже ${THRESHOLD}%"
    interrogate -v 2>&1 | tail -20
    exit 1
  fi
fi

# TypeScript — typedoc (если установлен)
if find . -name "*.ts" -not -path "*/\.*" -not -path "*/node_modules/*" 2>/dev/null | head -1 | grep -q .; then
  if [[ -f tsconfig.json ]] && command -v npx >/dev/null 2>&1; then
    echo "==> TypeScript JSDoc check"
    if npx -y typedoc --emit none --treatWarningsAsErrors 2>&1 | tail -5; then
      echo "✅ PASS: TypeScript JSDoc OK"
    else
      echo "⚠️  WARN: TypeScript JSDoc warnings (не блокируем)"
    fi
  fi
fi

echo "✅ PASS: docstring check completed"
