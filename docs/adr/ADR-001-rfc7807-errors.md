# ADR-001: Единый формат ошибок RFC 7807
Дата: 2025-10-22
Статус: Accepted

## Context
Непоследовательные ошибки → утечки деталей/стектрейсов, сложность корелляции инцидентов. Требуется совместимый с RFC 7807 ответ и корреляция по `X-Request-ID`.

## Decision
- Добавить глобальные handlers: `HTTPException`, `RequestValidationError`, `Exception`.
- Формат: `application/problem+json` с полями `type`, `title`, `status`, `detail`, `instance`, `correlation_id`. Для 422 — массив `errors`.
- `X-Request-ID` принимаем из запроса или генерируем; возвращаем в заголовке ответа и вкладываем в тело ошибок.

## Alternatives
- Оставить дефолтные fastapi-ответы — **минусы**: неунифицированно, нет correlation_id.
- Свой произвольный формат — **минусы**: несовместим со сторонними клинетами.

## Consequences (Security impact)
+ Маскирование внутренних деталей, трассировок.
+ Улучшенная наблюдаемость и разбор инцидентов.
± Доп. работа в тестах (проверка медиа-типа, ключей).

## Rollout
1. Включить handlers в `app/main.py`.
2. Добавить pytest для 404/422/500.
3. Обновить документацию API.

## Links
- NFR-02 (ошибки), NFR-05 (логирование)
- Risks: R3, R8
- tests: `tests/test_errors.py`, `tests/test_request_id.py`
