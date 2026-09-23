---
name: code2docs-data-model
description: Reverse-engineer the data model / ERD (entities, fields, keys, relations, enums, where data is stored and which components read or write it) from ORM models, SQL migrations/DDL, schemas or a RAG index, and render it as Mermaid erDiagram, PlantUML or draw.io. Use when the user asks for a data model, ERD, entity diagram, database schema documentation. Part of the code2docs skill family.
---

# Data model / ERD

Output: `<output>/data-model.md` (+ `data-model-<n>.puml` / `data-model.drawio` when selected).

## 0. Setup

Same as every code2docs sub-skill: read `code2docs-brief.md` from the output directory; if missing, ask for source + location, detail level, notation(s), output directory and create the brief (`../code2docs/templates/brief.md`), then gather evidence (`../code2docs/SKILL.md` step 3). Follow `../code2docs/references/detail-levels.md`, `sources.md`, `notations.md`.

## 1. Collect

Evidence priority (highest first):
1. SQL migrations / DDL (`CREATE TABLE`, `ALTER TABLE`) — the latest migration wins.
2. ORM models (inventory `orm_models`: SQLAlchemy/Django, JPA, EF Core `DbSet`, TypeORM, Prisma, Mongoose, GORM).
3. Contract schemas (JSON Schema, Avro, protobuf messages, OpenAPI components) — for message/DTO models.
4. RAG: query "database tables entities data model schema", then per entity.

For each entity capture: name, physical table/collection, store (which DB), fields (name, type, PK/FK/unique, nullable, default), relations with cardinality, enums/value sets, and which components read/write it (from `databases` findings and repository/DAO classes).

Separate **persistent entities** from **DTOs/messages**; include DTOs only at Deep level or if the user asks.

## 2. Write `data-model.md`

```markdown
# <System> — Data model
Source · Level · Date

## Summary          <stores used, number of entities, core aggregates>
## Stores           | Store | Technology | Entities | Evidence |
## ER diagram       <one per store or per aggregate if > ~25 entities>
## Entities
### <Entity>
Table: `<table>` · Store: <db> · Evidence: <file:line>
<one-line meaning in business terms>
| Field | Type | Key | Null | Description | Evidence |      (Standard: key fields only; Deep: all)
Relations: <Entity> 1..* <Other> via <fk>
Written by: <component> · Read by: <component>
## Enumerations     (Deep)
## Open questions   <e.g. tables in migrations without ORM model, unclear FKs>
```

Level specifics:
- **Overview**: entities + relations only; no field tables; one diagram.
- **Standard**: key fields (PK, FK, business identifiers, status fields); cardinalities.
- **Deep**: all fields, constraints, indexes, enums, read/write matrix `| Entity | Component | C | R | U | D |`.

## 3. Diagram

Mermaid `erDiagram` (types in field lines only at Standard/Deep), PlantUML `entity`, draw.io tables (`shape=table` or swimlane with one row per field). Relation cardinality must match the evidence; if uncertain use `|o--o{` and flag it.

## 4. Check

- [ ] Every entity has a store and evidence.
- [ ] FKs point to existing entities.
- [ ] Diagram and entity sections list the same entities.
