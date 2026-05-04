<!--
PR template Романа. Не удаляйте секции — оставляйте пустыми если не применимо.
Заполняется при `gh pr create` или через UI.
-->

## Что
<!-- Что делает PR с точки зрения пользователя/системы. Одной фразой. -->

## Почему
<!-- Контекст: какую задачу/проблему решаем. Ссылка на ADR в decisions/ или Roman PMO задачу. -->

- Связано с: [Roman PMO #N](https://github.com/users/rkazakov891/projects/1)
- ADR: `decisions/<file>.md` (если есть)

## Как тестировать

```bash
# Команда для проверки + ожидаемый результат
```

## Чек-лист

- [ ] Тесты добавлены/обновлены и проходят локально
- [ ] Линтер/форматтер pass (`ruff check . && ruff format --check .` для Python)
- [ ] Type-check pass (`mypy` если применимо)
- [ ] `ARCHITECTURE.md` обновлён (если архитектурный шов)
- [ ] `RESOURCES.md` обновлён (если новый URL/аккаунт/секрет)
- [ ] ADR создан в `decisions/` (если нетривиальное решение)
- [ ] `CHANGELOG.md` или `docs/changelog.md` обновлён
- [ ] Docs-gate локально PASS (`bash ~/.claude/scripts/run-docs-gate.sh main`)

## Rollback

<!-- Как откатить если что-то пойдёт не так. "git revert <sha>" не считается планом — нужны конкретные шаги. -->

## Скриншоты / артефакты (если UI)

<!-- Прикрепить before/after для визуальных изменений. -->

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
