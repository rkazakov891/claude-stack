# claude-stack

Meta-репозиторий персональной Claude Code инфраструктуры **Романа Казакова** для работы над несколькими проектами одновременно с AI-агентом.

## Что внутри

```
claude-stack/
├── .github/workflows/        ← reusable workflows для CI/CD
│   ├── docs-build.yml        ← билд MkDocs документации
│   ├── docs-gate.yml         ← проверки наличия ADR/docstrings/changelog
│   ├── docs-publish-pages.yml ← deploy на GitHub Pages через mike
│   └── release.yml           ← snapshot версии при git tag
│
├── templates/
│   ├── project-docs/         ← ARCHITECTURE.md + decisions/ (Karpathy-style)
│   └── mkdocs-project/       ← полная MkDocs Material структура
│       ├── mkdocs.yml        ← конфиг (порт 8765 локально)
│       ├── requirements-docs.txt
│       ├── Dockerfile.docs   ← локальный dev в Docker
│       ├── docker-compose.docs.yml
│       ├── docs/             ← структура: architecture, decisions, user-guide,
│       │                        development, api, releases, changelog
│       └── scripts/start-docs.sh
│
└── scripts/
    └── docs-gate/            ← локальные docs-gate проверки
        ├── check-adr.sh
        ├── check-docstrings.sh
        ├── check-changelog.sh
        ├── ai-fallback.sh
        └── run-all.sh
```

## Использование

В каждом проекте создаётся `.github/workflows/docs.yml`, который вызывает reusable:

```yaml
name: Docs
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  release:
    types: [published]

jobs:
  gate:
    if: github.event_name == 'pull_request'
    uses: rkazakov891/claude-stack/.github/workflows/docs-gate.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    with:
      ai-fallback: true

  build:
    if: github.event_name == 'push'
    uses: rkazakov891/claude-stack/.github/workflows/docs-build.yml@main

  publish:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: build
    uses: rkazakov891/claude-stack/.github/workflows/docs-publish-pages.yml@main

  release:
    if: github.event_name == 'release'
    uses: rkazakov891/claude-stack/.github/workflows/release.yml@main
```

## Локальный запуск документации

```bash
# Из проекта со скопированным mkdocs шаблоном
bash scripts/start-docs.sh
# Откроется http://localhost:8765
```

Через Docker:

```bash
docker compose -f docker-compose.docs.yml up
```

## Принципы (Karpathy-style)

- **Markdown-first** — никаких внешних БД для знаний
- **Compiler, not retriever** — документация компилируется один раз, не переоткрывается
- **Idea files** — самодостаточные паттерны, чужой агент адаптирует
- **Bookkeeping автомат, курация ручная** — AI пишет черновики, Роман правит

## Связанные репозитории

- [Roman PMO Project Board](https://github.com/users/rkazakov891/projects/1) — единый канбан всех проектов
- Проекты живут в `G:/Projects/` локально

## Лицензия

Личная инфраструктура. Используйте на свой страх и риск.
