# ADR-004: Идемпотентность POST /topics через уникальность
Дата: 2025-10-22
Статус: Accepted

## Context
Повторы запросов/реигрыши создают дубликаты записей.

## Decision
- Уникальный индекс на `(title, deadline)` — `uq_title_deadline`.
- На конфликт возвращаем **409 problem+json**.

## Alternatives
- Заголовок `Idempotency-Key` + сторедж — **плюс**: универсально, **минус**: хранилище/TTL сложнее.
- Только прикладная проверка без индекса — **минус**: гонки.

## Consequences
+ Простая гарантия целостности.
− Менее гибко, чем `Idempotency-Key`.

## Rollout
- Миграция (для SQLite — recreate), тест `tests/test_duplicate_and_delete.py`.

## Links
- Risks: R4; NFR-08
