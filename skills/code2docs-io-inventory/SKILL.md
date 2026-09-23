---
name: code2docs-io-inventory
description: Build an inventory of every application input and output (HTTP/gRPC/GraphQL APIs, UI, CLI arguments, environment/config, files and object storage, databases, message queues/topics, outbound API calls, e-mail/notifications, scheduled jobs) from a code repository or RAG index, with evidence. Use when the user asks "what are the inputs and outputs", "list interfaces/integrations", "what does this app read and write". Part of the code2docs skill family; usually called by the code2docs skill.
---

# Inputs / outputs inventory

Output: `<output>/io-inventory.md` (+ diagram files if a notation other than Mermaid is selected).

## 0. Setup (shared by all code2docs sub-skills)

1. Look for `code2docs-brief.md` in the output directory the user mentioned (or ask for it). If found, use its settings and evidence in `.code2docs/`.
2. If no brief: ask the user (structured question tool if available, otherwise in chat, then wait) for: source type + location, detail level (Overview/Standard/Deep), diagram notation(s), output directory. Write a brief from `../code2docs/templates/brief.md`, then gather evidence as described in `../code2docs/SKILL.md` step 3.
3. Rules: `../code2docs/references/detail-levels.md`, `../code2docs/references/sources.md` (citations), `../code2docs/references/notations.md` (diagrams).

## 1. Collect

Start from inventory categories `entrypoints, http_routes, cli_args, env_vars, file_io, databases, orm_models, messaging, http_clients, schedulers, ui_routes, contracts` (or RAG queries 5–11 of the query plan). For each candidate, open the code and determine:

- **Channel** — REST, gRPC, GraphQL, WebSocket, UI, CLI, env/config, file, object storage, DB, queue/topic, outbound API, e-mail/SMS/push, schedule/timer.
- **Direction** — Input (enters the app), Output (leaves the app), Both (e.g. DB read/write, request/response).
- **Counterpart** — who/what is on the other side (user role, system name, bucket, table, topic).
- **Data** — what is carried (entity/message name; fields at Deep level), format (JSON, CSV, Avro, protobuf, HTML…).
- **Trigger** — what causes it (user request, message arrival, cron, startup).
- **Evidence** — `file:line` / `[rag:…]`.

Group duplicates (same topic used in 5 places = one row, list the main locations). Remove test-only and dead code unless asked.

## 2. Write `io-inventory.md`

```markdown
# <System> — Inputs and outputs
Source: <...> · Level: <...> · Date: <...>

## Summary
<3–6 sentences: main input channels, main outputs, key external counterparts.>

## Context diagram
<diagram: system in the middle, inputs on the left, outputs on the right, grouped by channel>

## Inputs
| # | Channel | Name | Counterpart | Data / format | Trigger | Evidence |

## Outputs
| # | Channel | Name | Counterpart | Data / format | Trigger | Evidence |

## Configuration
| Variable / key | Purpose | Required | Default | Evidence |   <- values never copied if secret

## Scheduled / background jobs
| Job | Schedule | Reads | Writes | Evidence |

## Open questions
```

Level specifics:
- **Overview**: one row per channel+counterpart; skip Configuration table (mention count only).
- **Standard**: one row per endpoint/topic/table/file/env var group.
- **Deep**: one row per individual operation; add a "Fields" sub-table or link to `api-spec.md` / `data-model.md`; include validation rules and error outputs (HTTP error codes, dead-letter queues, error files).

## 3. Diagram

Context diagram per `notations.md`: actors/sources on the left → system (at Standard/Deep split into containers) → stores/queues/external systems on the right. Edge label = data + protocol. Produce in every selected notation.

## 4. Check before finishing

- [ ] Every row has evidence or *(inferred)*.
- [ ] Each inventory category was reviewed (write "none found" for empty ones).
- [ ] No secret values copied.
- [ ] Diagram elements match the tables.
