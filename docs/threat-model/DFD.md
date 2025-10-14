# DFD — Study Plan App (Exact to Code, GitHub‑safe)

This DFD matches the provided code: a single FastAPI app (`app.main`), logging middleware, SQLAlchemy to a local SQLite DB (`studyplan.db`). No API Gateway or extra services.

## Level 0 — Context

```mermaid
flowchart LR

  %% External actor
  U[User]

  %% Client boundary
  subgraph CLIENT[Trust Boundary: Client]
    UI[Web or Mobile Client]
  end

  %% Core boundary
  subgraph CORE[Trust Boundary: Core]
    APP[FastAPI Study Plan App]
  end

  %% Data boundary
  subgraph DATA[Trust Boundary: Data]
    DB[(SQLite studyplan.db)]
    LOG[(Logs stdout or file)]
  end

  %% Flows
  U -->|F1 User actions| UI
  UI -->|F2 HTTPS JSON| APP
  APP -->|F3 SQL via SQLAlchemy| DB
  APP -->|F4 HTTPS JSON response| UI
  APP -->|F5 Log request and response| LOG
```

---

## Level 1 — Processes and Endpoints

Processes reflect your endpoints and middleware exactly:

- P1: POST /topics
- P2: GET /topics
- P3: GET /topics/:id
- P4: PUT /topics/:id/progress
- P5: DELETE /topics/:id
- MW: Logging Middleware (wraps all requests and responses)

```mermaid
flowchart LR

  subgraph CLIENT[Trust Boundary: Client]
    UI[Web or Mobile Client]
  end

  subgraph CORE[Trust Boundary: Core]
    MW[Logging Middleware]
    P1[Process P1 POST /topics]
    P2[Process P2 GET /topics]
    P3[Process P3 GET /topics/:id]
    P4[Process P4 PUT /topics/:id/progress]
    P5[Process P5 DELETE /topics/:id]
  end

  subgraph DATA[Trust Boundary: Data]
    DB[(SQLite topics table)]
    LOG[(Logs)]
  end

  %% Client -> Middleware
  UI -->|F6 HTTPS JSON| MW

  %% Middleware dispatch to processes
  MW -->|F7 dispatch to P1| P1
  MW -->|F8 dispatch to P2| P2
  MW -->|F9 dispatch to P3| P3
  MW -->|F10 dispatch to P4| P4
  MW -->|F11 dispatch to P5| P5

  %% Processes <-> DB
  P1 -->|F12 INSERT Topic| DB
  P2 -->|F13 SELECT All Topics| DB
  P3 -->|F14 SELECT Topic by Id| DB
  P4 -->|F15 UPDATE Progress by Id| DB
  P5 -->|F16 DELETE Topic by Id| DB

  %% Responses back through middleware
  P1 -->|F17 201 JSON Topic| MW
  P2 -->|F18 200 JSON List| MW
  P3 -->|F19 200 or 404 JSON| MW
  P4 -->|F20 200 JSON Status OK| MW
  P5 -->|F21 200 JSON Status Deleted| MW
  MW -->|F22 HTTPS JSON| UI

  %% Logs
  MW -->|F23 Request and Response Logs| LOG
```

---

## Flows Summary (F1…F23)

| ID  | From             | To                 | Data                              | Channel              |
|-----|------------------|--------------------|-----------------------------------|----------------------|
| F1  | User             | Client             | UI interactions                   | UI                   |
| F2  | Client           | FastAPI App        | HTTP request JSON                 | HTTPS                |
| F3  | FastAPI App      | SQLite             | SQL CRUD                          | Local driver         |
| F4  | FastAPI App      | Client             | HTTP response JSON                | HTTPS                |
| F5  | FastAPI App      | Logs               | Request and response log lines    | stdout or file       |
| F6  | Client           | Middleware         | HTTP request JSON                 | HTTPS                |
| F7  | Middleware       | P1                 | Dispatch                          | in process           |
| F8  | Middleware       | P2                 | Dispatch                          | in process           |
| F9  | Middleware       | P3                 | Dispatch                          | in process           |
| F10 | Middleware       | P4                 | Dispatch                          | in process           |
| F11 | Middleware       | P5                 | Dispatch                          | in process           |
| F12 | P1               | SQLite             | INSERT Topic                      | SQL                  |
| F13 | P2               | SQLite             | SELECT all                        | SQL                  |
| F14 | P3               | SQLite             | SELECT by id                      | SQL                  |
| F15 | P4               | SQLite             | UPDATE progress                   | SQL                  |
| F16 | P5               | SQLite             | DELETE by id                      | SQL                  |
| F17 | P1               | Middleware         | 201 JSON Topic                    | in process           |
| F18 | P2               | Middleware         | 200 JSON List                     | in process           |
| F19 | P3               | Middleware         | 200 or 404 JSON                   | in process           |
| F20 | P4               | Middleware         | 200 JSON Status OK                | in process           |
| F21 | P5               | Middleware         | 200 JSON Status Deleted           | in process           |
| F22 | Middleware       | Client             | HTTP response JSON                | HTTPS                |
| F23 | Middleware       | Logs               | Log lines                         | stdout or file       |

---

## Notes

- This mirrors the exact code: single app, middleware, SQLite. No gateway.
- Mermaid is GitHub-safe: ASCII only, blank line after `flowchart LR`, one edge per line, no braces in labels.
- You can extend later with CORS, auth, or migrations; then update the DFD accordingly.
