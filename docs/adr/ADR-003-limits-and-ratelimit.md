# ADR-003: Лимиты тела и Rate Limit per-IP
Дата: 2025-10-22
Статус: Accepted

## Context
Большие payload'ы и отсутствие квот → рост латентности/памяти и деградации.

## Decision
- Middleware лимита тела по `Content-Length` (ENV `APP_MAX_BODY_BYTES`, по умолчанию 2 MiB) → **413 problem+json**.
- Простой rate-limit per-IP: ENV `APP_RATE_LIMIT_RPM` (0 = выключено) → **429 problem+json**.

## Alternatives
- Вынести rate-limit на ingress только — **плюс**: надёжно, **минус**: локальная разработка и автотесты сложнее.
- Библиотеки-боттлы (slowapi) — **плюс**: готово, **минус**: лишняя зависимость.

## Consequences
+ Быстрые «предохранители».
− Возможны ложные срабатывания при NAT/прокси → параметризуем через ENV.

## Rollout
- Middleware в `app/main.py`, тесты `tests/test_body_limit.py`, `tests/test_rate_limit.py`.

## Links
- Risks: R5, R6; NFR-06
