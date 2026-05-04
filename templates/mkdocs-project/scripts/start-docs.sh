#!/usr/bin/env bash
# Запуск локального dev-сервера MkDocs на порту 8765
# Не использует docker — для быстрой проверки
# Если нужен Docker — `docker compose -f docker-compose.docs.yml up`

set -e

PORT=8765

# Проверка занятости порта
if command -v lsof >/dev/null 2>&1; then
  if lsof -i :"$PORT" >/dev/null 2>&1; then
    echo "ОШИБКА: порт $PORT уже занят. Проверьте memory/ports.md"
    exit 1
  fi
fi

# Проверка установки mkdocs
if ! command -v mkdocs >/dev/null 2>&1; then
  echo "Устанавливаю зависимости..."
  pip install -r requirements-docs.txt
fi

echo "==> Запускаю MkDocs на http://localhost:$PORT"
echo "    (Ctrl+C для остановки)"
mkdocs serve --dev-addr="0.0.0.0:$PORT"
