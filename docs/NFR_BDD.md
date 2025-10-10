# Study Plan App — Security NFR BDD Acceptance Scenarios

## Цель
Подтвердить выполнение нефункциональных требований безопасности (Security NFR) для **Study Plan App**.
Сценарии оформлены в стиле **BDD (Given / When / Then)** и покрывают работу с базой данных:
ORM‑безопасность, консистентность транзакций, защиту от SQL‑инъекций, уникальность данных и корректные дефолты.
Из 5 сценариев — 2 негативных.

---

## Scenario 1 — Только ORM-операции, без raw SQL (NFR-DB-01)

**Feature:** ORM Safety
**ID:** NFR-DB-01

```gherkin
Scenario: Все запросы к базе выполняются только через ORM
  Given приложение использует SQLAlchemy для доступа к базе данных
  When выполняются CRUD-операции с таблицей topics
  Then в кодовой базе отсутствуют прямые вызовы .execute() или raw SQL
  And все операции фиксируются через ORM-команды add(), commit(), delete()
```
Метрика/Порог: **100%** запросов через ORM.
Проверка: grep/статический анализ + code review.

---

## Scenario 2 — Консистентность транзакций при удалении (NFR-DB-02)

**Feature:** Transaction Consistency
**ID:** NFR-DB-02

```gherkin
Scenario: Удалённая запись недоступна после удаления
  Given в базе существует тема с id = 10
  When выполняется DELETE /topics/10
  And затем GET /topics/10
  Then сервер возвращает 404 Not Found
  And запись отсутствует в таблице topics
```
Метрика/Порог: **100%** корректных транзакций.
Проверка: pytest (delete → get).

---

## Scenario 3 — Защита от SQL-инъекций (NFR-DB-03) — негативный

**Feature:** SQL Injection Protection
**ID:** NFR-DB-03

```gherkin
Scenario: Попытка SQL-инъекции не приводит к выполнению опасного кода
  Given клиент отправляет POST /topics с title = "'; DROP TABLE topics;--"
  When ORM обрабатывает входные данные
  Then таблица topics остаётся доступной
  And существующие записи не изменены
  And сервер возвращает безопасную ошибку валидации (4xx) без утечки деталей БД
```
Метрика/Порог: **0** успешных SQL-инъекций.
Проверка: pytest негативный тест + ручной чек.

---

## Scenario 4 — Уникальность названий тем (NFR-DB-04) — негативный

**Feature:** Data Integrity (Uniqueness)
**ID:** NFR-DB-04

```gherkin
Scenario: Повторное создание темы с тем же title блокируется
  Given в базе существует тема с title = "Algebra"
  When клиент повторно вызывает POST /topics с title = "Algebra"
  Then сервер возвращает 409 Conflict (или 422 Validation Error)
  And в таблице topics остаётся только одна запись с title = "Algebra"
```
Метрика/Порог: **100%** предотвращённых дублей.
Проверка: pytest (create duplicate → conflict).

---

## Scenario 5 — Корректные дефолты и ограничения схемы (NFR-DB-05)

**Feature:** Schema Defaults & Constraints
**ID:** NFR-DB-05

```gherkin
Scenario: Новая тема получает корректные дефолтные значения и проходит ограничения
  Given клиент отправляет POST /topics с валидным title и без progress
  When запись создаётся через ORM
  Then в базе progress по умолчанию равен 0
  And поле title не пустое (NOT NULL / min_length > 0)
  And при попытке записать progress вне диапазона 0..100 сервер возвращает 422
```
Метрика/Порог: **100%** корректных дефолтов и отказов при нарушении ограничений.
Проверка: pytest (валидные и граничные значения).

---

## Примечания к приёмке
- Сценарии ориентированы на текущее API `/topics` и модель `Topic(id, title, deadline, progress)`.
- Негативные сценарии: **SQL-инъекция** и **дубликаты title**.
- В отчётах приёмки фиксируются фактические коды ответов и состояние БД до/после.
