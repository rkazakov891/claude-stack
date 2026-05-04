# Conventions для всех проектов Романа

## Conventional Commits

Формат сообщения коммита:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types (обязательно)

| Type | Когда использовать |
|------|--------------------|
| `feat` | Новая функциональность для пользователя |
| `fix` | Исправление бага |
| `docs` | Только документация (ARCHITECTURE/RESOURCES/decisions/README/comments) |
| `refactor` | Код без смены семантики (rename, extract method, реорг) |
| `test` | Добавление/правка тестов |
| `chore` | Рутина (deps, конфиги, .gitignore, шаблоны) |
| `perf` | Оптимизация производительности |
| `ci` | CI/CD pipeline (.github/workflows/) |
| `build` | Build system (Dockerfile, package.json scripts, pyproject) |
| `style` | Форматирование без смены кода (whitespace, точка с запятой) |
| `revert` | Откат предыдущего коммита |

### Scope (опционально)

Модуль/компонент верхнего уровня в нижнем регистре:
- `feat(auth): добавил OAuth провайдер Google`
- `fix(api): обработка пустого тела запроса`
- `docs(arch): уточнил инвариант про порт 80`

Если затронуто несколько scope или scope unclear — пропустить:
- `refactor: вынес общую логику в utils`

### Subject (обязательно)

- Повелительное наклонение: "добавил" / "исправил" / "обновил"
- До 72 символов
- Без точки в конце
- На русском (внутренние коммиты Романа); на английском — если опенсорс

### Body (опционально, после пустой строки)

- Что и почему (не как — это видно в diff)
- До 100 символов на строку
- Можно multiline

### Footer (опционально)

- `BREAKING CHANGE: <описание>` — для несовместимых изменений
- `closes Roman PMO #N` — закрытие задачи на канбане
- `co-authored-by: Имя <email>`

### Примеры

```
feat(tasks): /tasks autopilot — последовательное выполнение задач

Цикл pick-next → work → done без апрувов между задачами.
Останавливается на FAIL ship-gate или пустом Backlog.

closes Roman PMO #14
```

```
fix(docs-gate): корректное определение архитектурных изменений

Раньше любой новый файл в src/ триггерил ADR-check. Теперь только
изменения публичных API (def public_, class, export).
```

```
chore: bootstrap pmo-test
```

## Формат имени ветки

```
<type>/<slug>           # для самостоятельных задач (feat/oauth-google)
<task-id>-<slug>        # для задач с канбана Roman PMO (PVTI_xxx-onboarding)
```

`main` — protected, не коммитим напрямую.

## Связь коммитов с задачами Roman PMO

В footer коммита: `closes Roman PMO #<task-id>` или `refs Roman PMO #<task-id>`.

При merge PR с таким footer'ом — задача автоматически переходит в Done через `/ship-gate` (skill вытаскивает item-id из footer'а).
