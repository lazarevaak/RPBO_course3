# ADR-002: Жёсткий CORS allowlist
Дата: 2025-10-22
Статус: Accepted

## Context
Широкий CORS приводит к межсайтовому злоупотреблению браузерными токенами.

## Decision
- `allow_origins` — только список из ENV `CORS_ALLOWED_ORIGINS` (или дефолты).
- Запрещаем `allow_credentials=true`.
- Тесты: preflight с чужого Origin — без `Access-Control-Allow-Origin`; с разрешенного — заголовок присутствует.

## Alternatives
- `*` — **минусы**: высокий риск.
- Динамический референс по БД — **минусы**: сложность, кеширование.

## Consequences
+ Снижение поверхности атак.
− Поддержка списка через конфиг.

## Rollout
- Конфиг в ENV, тесты `tests/test_cors.py`.

## Links
- Risks: R2; NFR-10 (предлагаемый)
