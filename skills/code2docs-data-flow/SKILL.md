---
name: code2docs-data-flow
description: Produce data flow diagrams (DFD level 0/1/2) and data flow descriptions showing how data enters, is transformed, stored and leaves an application, derived from a code repository or RAG index, rendered in Mermaid, PlantUML or draw.io. Use when the user asks for data flows, data lineage, "how does data move through the system", DFD or information flow. Part of the code2docs skill family.
---

# Data flow

Output: `<output>/data-flow.md` (+ `data-flow-<n>.puml`, `data-flow.drawio` when selected).

## 0. Setup

Same as every code2docs sub-skill: read `code2docs-brief.md` from the output directory; if missing, ask for source + location, detail level, notation(s), output directory, create the brief (`../code2docs/templates/brief.md`) and gather evidence (`../code2docs/SKILL.md` step 3). Follow `../code2docs/references/detail-levels.md`, `sources.md`, `notations.md`.

Reuse `io-inventory.md`, `data-model.md`, `block-diagram.md` if present — the external entities, stores and processes must use the same names.

## 1. Model the flows

DFD elements:
- **External entity** — user role or external system (source/sink of data).
- **Process** — something that transforms data (endpoint handler, consumer, job, pipeline step). Number them: `P1`, `P1.1`…
- **Data store** — DB table group, cache, file location, bucket, queue/topic (queues may be drawn as stores).
- **Data flow** — labelled arrow with the *data item name* (e.g. `order request`, `OrderCreated event`, `invoice PDF`).

How to find flows in code: start at every input from the inventory, follow the handler → service → repository/client calls, noting each read, transformation (mapping, validation, enrichment, aggregation) and write/emit. For RAG, use "input files", "output reports", "events", "integrations" queries and process descriptions.

## 2. Levels

| Level | DFDs |
|---|---|
| Overview | Level 0 (context): one process = the system; external entities; major flows |
| Standard | Level 0 + Level 1: 4–10 major processes and data stores |
| Deep | Level 0 + 1 + Level 2 for each Level-1 process with ≥3 sub-steps; plus flow detail tables |

## 3. Write `data-flow.md`

```markdown
# <System> — Data flows
Source · Level · Date

## Level 0 — Context
<diagram>
## Level 1 — Main processes
<diagram>
### Processes
| ID | Process | Description | Inputs | Outputs | Code location | Evidence |
### Data stores
| ID | Store | Technology | Holds | Written by | Read by | Evidence |
## Level 2 — P<n> <name>             (Deep)
<diagram + table>
## Flow details                       (Standard: main flows; Deep: all)
| # | From | To | Data | Format | Trigger | Sync/async | Evidence |
## Sensitive data                     (if found: PII, payment, credentials — where it flows and is stored)
## Open questions
```

## 4. Diagram rules

- Mermaid `flowchart LR`: entities `(("…"))`, processes `["P1 …"]`, stores `[("…")]`, queues `[["…"]]`, files `[/"…"/]`; every edge labelled with the data item.
- PlantUML: `actor`/`rectangle`/`database`/`queue`/`file` with labelled `-->`.
- draw.io: styles from the skeleton; left-to-right layout.
- Processes must have at least one input and one output flow; data never flows store→store or entity→store directly (insert the process).

## 5. Check

- [ ] Every inventory input reaches at least one process; every output originates from a process.
- [ ] Level-1 flows are consistent with Level-0 flows (balanced).
- [ ] Names match `block-diagram.md` / `data-model.md`.
