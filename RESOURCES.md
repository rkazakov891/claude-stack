# Ресурсы — claude-stack

> Реестр ресурсов meta-репозитория персональной Claude Code инфраструктуры.

## Репозитории

| Что | Ссылка | Заметки |
|-----|--------|---------|
| Main repo | <https://github.com/rkazakov891/claude-stack> | публичный, default branch `main` |
| Локально | `G:/Projects/claude-stack/` | основная рабочая копия |
| Cache клон | `~/.claude/cache/claude-stack/` | для скриптов и hooks |

## URL и адреса

| Среда | URL | Когда работает |
|-------|-----|----------------|
| GitHub repo | <https://github.com/rkazakov891/claude-stack> | 24/7 |
| GitHub Pages docs (если включить) | `https://rkazakov891.github.io/claude-stack/` | пока не настроено |
| Local dev (для docs) | http://localhost:8765 | вручную через `bash scripts/start-docs.sh` |

## API endpoints

— нет (это репозиторий шаблонов, не сервис)

## Внешние сервисы и аккаунты

| Сервис | Назначение | Аккаунт | Линки |
|--------|-----------|---------|-------|
| GitHub | хостинг + Actions | rkazakov891 | <https://github.com/rkazakov891> |
| GitHub Projects (Roman PMO) | трекер задач | rkazakov891 | <https://github.com/users/rkazakov891/projects/1> |
| Anthropic API | LLM (для AI fallback в docs-gate, future) | — | <https://console.anthropic.com> |

## Установленные приложения / зависимости

| Приложение | Версия | Назначение |
|-----------|--------|-----------|
| GitHub CLI (`gh`) | 2.92 | scripted GH operations |
| Git | system | VCS |
| Bash (Git Bash) | system | shell для скриптов |
| Python | 3.12 | для MkDocs (когда билдим документацию) |
| Docker | 4.x+ | опционально, для `docker-compose.docs.yml` |

## Ссылки на документацию

### Внутренняя
- [README.md](./README.md) — обзор репозитория
- [templates/mkdocs-project/](./templates/mkdocs-project/) — MkDocs Material шаблон
- [templates/project-docs/](./templates/project-docs/) — Karpathy-style документация
- [.github/workflows/](./.github/workflows/) — reusable workflows
- [scripts/docs-gate/](./scripts/docs-gate/) — docs-gate проверки

### Внешняя
- MkDocs Material: <https://squidfunk.github.io/mkdocs-material/>
- Mike (versioning): <https://github.com/jimporter/mike>
- GitHub Actions reusable workflows: <https://docs.github.com/en/actions/using-workflows/reusing-workflows>
- GitHub Projects API: <https://docs.github.com/en/issues/planning-and-tracking-with-projects>

## Реестр секретов (БЕЗ самих значений)

| Имя | Где хранится | Где используется |
|-----|--------------|------------------|
| `GITHUB_TOKEN` | автоматически в Actions | reusable workflows |
| `ANTHROPIC_API_KEY` | secret в репо проекта-потребителя | docs-gate AI fallback |

> Сам `claude-stack` не хранит секретов — это шаблоны и workflows.

## Стейкхолдеры

| Имя | Роль |
|-----|------|
| Роман Казакова | Owner, единственный пользователь |

## Каналы коммуникации

| Канал | Назначение |
|-------|-----------|
| GitHub Issues | <https://github.com/rkazakov891/claude-stack/issues> |
| Roman PMO board | <https://github.com/users/rkazakov891/projects/1> |

## Связанные проекты

Используют шаблоны и workflows из этого репо:
- pmo-test (pilot) — <https://github.com/rkazakov891/pmo-test>
- (по мере распространения) ProstoVC, SelectiveAI

---

> Правило: при появлении нового шаблона / workflow / интеграции — добавлять сюда сразу.
