---
name: code2docs-sequence
description: Produce sequence diagrams for the key use cases of an existing application - request handling, event processing, batch jobs, including async messages and error paths - traced from the code repository or RAG index, in Mermaid or PlantUML (draw.io optional). Use when the user asks for sequence diagrams, interaction diagrams, call flows or "what happens when a user does X". Part of the code2docs skill family.
---

# Sequence diagrams

Output: `<output>/sequences.md` (+ `sequence-<nn>-<slug>.puml` / `sequences.drawio` when selected).

## 0. Setup

Same as every code2docs sub-skill: read `code2docs-brief.md` from the output directory; if missing, ask for source + location, detail level, notation(s), output directory, create the brief (`../code2docs/templates/brief.md`) and gather evidence (`../code2docs/SKILL.md` step 3). Follow `../code2docs/references/detail-levels.md`, `sources.md`, `notations.md`.

## 1. Pick use cases

Candidates: main HTTP operations (writes before reads), message consumers, scheduled jobs, login/auth, file imports/exports, RAG "use cases features" results.

| Level | How many | Participants | Paths |
|---|---|---|---|
| Overview | 1–3 | actor, system, external systems | happy path |
| Standard | 3–7 | actor, containers, stores, external systems | happy + main alt (validation failure, not found) |
| Deep | all significant | components/classes inside containers | + errors, retries, timeouts, transactions, async callbacks |

Propose the list to the user and let them add/remove before tracing (skip confirmation at Overview if obvious).

## 2. Trace

For each use case, start at the entry point (`file:line`) and follow calls in order: validation → service → repository/DB → outbound calls → messages published → response. Note:
- sync vs async (awaits, message publish, background task);
- transactions boundaries;
- conditional branches that change the outcome (`alt`), loops (`loop`), parallel calls (`par`);
- error handling (`try/catch`, error middleware, DLQ, retry policies).

Keep an evidence list per step.

## 3. Write `sequences.md`

```markdown
# <System> — Sequence diagrams
Source · Level · Date

## Use cases
| # | Use case | Trigger | Entry point | Evidence |

## 1. <Use case>
<one-paragraph description in business terms>
<diagram>
Steps:
| Step | From → To | Message / call | Evidence |
Notes: <assumptions, *(inferred)* steps>

## Open questions
```

## 4. Diagram rules

- Mermaid `sequenceDiagram` with `autonumber`; `actor` for people, `participant` for components, `participant X as "Orders DB"` for stores; `->>` sync call, `-->>` reply, `-)` async message; `alt/else/end`, `opt`, `loop`, `par`, `Note over`.
- PlantUML: `actor`, `participant`, `database`, `queue`; `->`, `-->`, `->>` async; `alt/else/end`, `group`.
- draw.io only if selected: lifelines as `shape=umlLifeline`, messages as edges; one page per use case.
- Participant names identical to `block-diagram.md`.
- ≤ ~20 messages per diagram; split long flows into "part 1/part 2".

## 5. Check

- [ ] Every message is backed by a call in code or RAG text (else *(inferred)*).
- [ ] Async messages are drawn as async.
- [ ] Error paths present at Standard/Deep where the code handles them.
