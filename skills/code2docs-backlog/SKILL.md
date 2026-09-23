---
name: code2docs-backlog
description: Act as a business analyst and turn a reverse-engineered specification (code2docs output or another spec) into a re-implementation backlog - epics, features and user stories with Gherkin acceptance criteria, field-level data mapping to legacy DB tables, REST APIs, SOAP web services, messages and files, validation rules and schemas, dependencies with implementation order, and gap/improvement stories. Use when the user wants user stories, a backlog, epics, requirements for rebuilding or migrating an existing application, or "stories we can implement elsewhere". Part of the code2docs skill family.
---

# Backlog from specification (business analyst)

Use case: **existing code → specification (code2docs) → backlog** that another team can implement on a different platform. Stories are **technology-agnostic** in behaviour, but every story states exactly **which legacy fields map** (DB columns, REST fields, SOAP elements, message fields, file columns, config keys), with **validation rules and schemas**, so nothing is lost in re-implementation.

Paths below are relative to this skill's folder. Templates: `templates/`. Shared rules: `../code2docs/references/sources.md` (citations).

## Step 0 — Interview (never skip)

Ask in rounds of at most 4 questions. Use a structured question tool if your agent has one (e.g. `AskUserQuestion`); otherwise ask in chat with numbered options and **wait**. Skip what the user already said.

1. **Specification source**
   - A folder with code2docs output (`code2docs-brief.md`, `product-spec.md`, `api-spec.md`, `data-model.md`, `io-inventory.md`, `sequences.md`, …). Check which files exist and their detail level (from the brief).
   - No spec yet → offer to run the `code2docs` skill first. Recommend **Deep** level with at least *product-spec, io-inventory, data-model, api-spec* (plus *sequences* for alternative/error paths) — stories need field-level mapping.
   - Another spec document (path) → use it; if it lacks field-level detail, ask for access to the code or RAG index to fill mapping tables, or mark mapping gaps as open questions.
2. **Scope** — all features, or selected epics/modules/features? Include **gap / improvement stories** (default: yes)?
3. **Personas** — use roles from the product spec (default), or a list the user gives. System actors are allowed for jobs and integrations ("As the billing system …").
4. **Output** — directory (default `<spec-dir>/backlog/`), document language, ID prefix (default `E`).

Confirm with a summary (spec source + level, scope, gap stories yes/no, personas, output dir) before writing.

If the spec is Standard/Overview level, warn that mapping tables will be incomplete; offer to deepen `data-model` / `api-spec` for the in-scope features first.

## Step 1 — Feature map

Read the spec documents fully. Build the hierarchy:

- **Epic** — a business capability (e.g. *Order management*, *Customer onboarding*). Usually one per product-spec feature group / bounded context. 4–12 epics for a typical application.
- **Feature** — a coherent function within the epic (e.g. *Create order*, *Cancel order*).
- **Story** — one user-visible behaviour that can be built, tested and demoed on its own (INVEST). Split by: operation, role, business-rule variant, channel (UI vs. API vs. batch), happy vs. exceptional handling when the exception is substantial. Merge trivial reads into the feature's main story.

Sources for stories: product-spec features, FRs and business rules; every provided API operation; every consumed integration; every scheduled job; every file import/export; every message consumer/producer; UI routes; reference-data maintenance.

Write the map as a table in `README.md` before writing stories, and (Standard/Deep specs) show it to the user for a quick check: *"Here are the N epics and M features — add, merge or drop anything?"*

## Step 2 — Write stories

Use `templates/epic.md` per epic file `epics/E<nn>-<slug>.md` and `templates/story.md` per story. Required parts:

1. **Header** `### E01-F02-S03 — <title>` · Type `Parity` or `Gap` · Labels.
2. **Statement** — *As a* <persona> *I want* <capability> *so that* <business value>.
3. **Description & business rules** — reference `BR-nn`/`FR-nn` from product-spec; restate the rule in plain language.
4. **Acceptance criteria (Gherkin)** — `Feature`/`Scenario` blocks:
   - happy path;
   - one scenario per validation rule (or a `Scenario Outline` with `Examples` table for many similar rules);
   - error and alternative paths taken from sequences / api-spec error codes;
   - authorisation (who may / may not);
   - side effects (records created/updated, messages published, notifications, files written).
   Wording is tech-agnostic: say "the order is saved with status *Pending*", not "INSERT into ORDERS" or "OrderRepository.save". Legacy names appear only in the mapping section.
5. **Data & interface mapping** — the key section. One row per field touched by the story:

   | Legacy source | Kind | Field / path | Business meaning | Type / format | Req. | Validation / constraints | Dir. | Evidence |
   |---|---|---|---|---|---|---|---|---|
   | `ORDERS` | DB column | `ORDERS.TOTAL_AMOUNT` | Order total incl. VAT | decimal(12,2), EUR | Y | ≥ 0; = sum(lines) | W | `db/V3__orders.sql:14` |
   | `POST /orders` | REST request | `$.customerId` | Ordering customer | UUID | Y | must exist, active | In | `api/orders.py:31` |
   | `OrderService.CreateOrder` | SOAP element | `CreateOrderRequest/Lines/Line/Qty` | Quantity | xs:int | Y | 1..999 | In | `wsdl/order.wsdl:88` |
   | `orders.created` | Message field | `payload.orderId` | Created order id | UUID | Y | — | Out | `events/producer.py:12` |

   Kinds: DB column, REST request / response / path / query / header, SOAP operation / element / fault, message field, file column / record, config key, UI field. Direction: In, Out, R (read), W (write), R/W. Take values from `data-model.md`, `api-spec.md`, `io-inventory.md`; open the code / RAG when the spec lacks a detail. If a story truly touches no data write "No data mapping — <reason>".
6. **Schemas** — link the relevant api-spec / data-model sections. When the spec is Deep, also embed a compact JSON Schema (or table) of each request/response/message payload so the story is self-contained. Include enumerations with all legacy values and their meaning.
7. **Validation rules** — consolidated table: field, rule, legacy error code/message, where enforced in legacy (UI / API / DB constraint / service). Mark rules enforced only in the UI or only by the DB — they are easy to lose.
8. **Integrations touched** — external systems by business role (e.g. *payment provider*), with the legacy protocol/endpoint as reference.
9. **Dependencies** — `Depends on: E01-F01-S01, E03-F01-S02` (reference data must exist, entity created by another story, auth, upstream integration). Write `Depends on: none` when there are none.
10. **Legacy evidence** — `path:line` / `[rag:…]` list for traceability.
11. **Open questions** and **Definition of Ready** checklist (from the template).

Quality bar for every story: INVEST, each AC testable, mapping covers every field mentioned in AC, no invented behaviour — anything not backed by evidence is *(inferred)* or an open question.

## Step 3 — Gap / improvement stories (if in scope)

While reading spec and code, collect issues and write them as `Gap` stories in `gaps.md` (and reference them from the affected epic):

- missing or inconsistent validation (same field validated differently in two places);
- unhandled errors, silent failures, missing retries/idempotency;
- security: hard-coded secrets (never copy the value), missing authorisation checks, sensitive data in logs;
- data quality: nullable fields that are business-mandatory, missing constraints, free-text codes;
- dead, duplicated or contradictory logic; documented-but-not-implemented and implemented-but-undocumented behaviour (code vs. RAG conflicts).

Each gap story has **Observed in legacy** (with evidence), **Impact**, **Recommended behaviour** and Gherkin AC for the recommended behaviour. Label clearly: *Not parity — decision needed by product owner*.

## Step 4 — Dependencies and implementation order

1. If Python is available, run
   `python3 <this-skill-dir>/scripts/check_backlog.py <backlog-dir> --spec <spec-dir> --write-order`
   It validates IDs and references, detects dependency cycles, computes **implementation waves** (Wave 1 = stories with no dependencies, Wave n = depends only on earlier waves) and writes them to `<backlog-dir>/implementation-order.md`. Fix every reported error and re-run until clean.
2. Without Python: list all `Depends on` edges, remove stories with no unresolved dependencies wave by wave by hand, and write the same `implementation-order.md`.
3. Add a Mermaid `flowchart LR` of **epic-level** dependencies to `README.md` (story-level graph only for Deep specs or on request; max ~40 nodes per graph).
4. Typical foundations in early waves: reference/master data, identity & roles, core entities, inbound integrations that other features consume.

## Step 5 — Coverage and traceability

Write `traceability.md`: every product-spec FR, every provided API/SOAP operation, every persisted entity, every I/O channel → story IDs → legacy evidence. Items without a story go to **Intentionally out of scope** (with reason) or become new stories. `check_backlog.py --spec` lists uncovered FR ids, operations and entities to help.

## Output

```
<backlog-dir>/
  README.md               scope, personas, epic/feature table, dependency graph, summary of waves, coverage, open questions
  epics/E01-<slug>.md      epic goal, features, all stories in full
  gaps.md                  gap / improvement stories
  implementation-order.md  waves (generated by the script or by hand)
  traceability.md          spec item → stories → legacy evidence
```

Use `templates/backlog-readme.md` for `README.md`.

## Final checklist

- [ ] Every story: statement, ≥1 Gherkin scenario, mapping table (or explicit "No data mapping"), dependencies line, evidence.
- [ ] Every validation rule from the spec appears in some story's AC and validation table.
- [ ] No cycles; waves computed; every dependency exists.
- [ ] Coverage: no spec item silently missing.
- [ ] No legacy technology leaks into statements/AC; legacy names only in mapping/evidence.
- [ ] No secrets copied.
- [ ] Tell the user: number of epics/features/stories/gap stories, number of waves, top open questions, where the files are.
