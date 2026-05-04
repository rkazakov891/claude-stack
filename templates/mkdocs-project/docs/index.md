# PROJECT_NAME

> PROJECT_DESCRIPTION

Это автоматически собираемая документация проекта. Все разделы рендерятся из markdown в `docs/`.

## Карта документации

- **[Архитектура](architecture/index.md)** — компоненты, потоки данных, инварианты
- **[Решения (ADR)](decisions/index.md)** — журнал архитектурных решений
- **[User Guide](user-guide/index.md)** — функциональная документация для пользователя
- **[Разработка](development/setup.md)** — setup, тестирование, contributing
- **[API](api/index.md)** — справочник публичных интерфейсов
- **[Релизы](releases/index.md)** — история версий, changelog

## Быстрый старт

```bash
# Локальный dev-сервер документации
bash scripts/start-docs.sh
# Откроется на http://localhost:8765
```

## Источники истины

| Что | Где |
|-----|-----|
| Архитектурное состояние | `docs/architecture/` |
| Решения "почему так" | `docs/decisions/` |
| Журнал работы | `log.md` (корень репо) |
| Канбан задач | [Roman PMO](https://github.com/users/rkazakov891/projects/1) |
