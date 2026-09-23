# Detail levels

Three levels. The chosen level applies to every document in the run unless the user overrides it for a single document.

| | Overview | Standard | Deep |
|---|---|---|---|
| Audience | business, stakeholders | architects, new team members | engineers, reviewers, auditors |
| Scope unit | whole system as one box | containers / deployable units / top modules | components, classes, functions |
| Evidence | citation per section | citation per table row where available | citation on every row and diagram element list |
| Diagrams | 1 per document | 1–3 per document | as many as needed; one per container/module |
| Length guide | 1–2 pages | 3–8 pages | no limit; split into files per module if > ~15 pages |

## Per document

**Product spec**
- Overview: purpose, users/roles, top features (≤10), key integrations.
- Standard: + feature descriptions, functional requirements derived from code (FR-nn), observed non-functional aspects (auth, logging, scaling, config), constraints.
- Deep: + acceptance-style rules per FR (validation rules, limits, error cases), traceability table FR → code/RAG evidence.

**I/O inventory**
- Overview: channels only (e.g. "REST API", "Kafka topic orders", "PostgreSQL"), direction, purpose.
- Standard: every endpoint/topic/table/file/env var group, with format and counterpart system.
- Deep: every individual input and output with fields/types, validation, file:line, triggering code path.

**Data flow**
- Overview: DFD level 0 (context): system + external entities + main flows.
- Standard: level 1: major processes and data stores.
- Deep: level 2 per major process, with data item names on every edge.

**Block diagram**
- Overview: C4 System Context.
- Standard: + C4 Container.
- Deep: + C4 Component for each container (and key classes where relevant).

**Sequence diagrams**
- Overview: 1–3 most important use cases, happy path only, system-level participants.
- Standard: 3–7 use cases, container-level participants, main alternative paths.
- Deep: all significant use cases, component-level participants, error/retry/timeout paths, async messages.

**Data model**
- Overview: main entities and relations, no fields.
- Standard: entities with key fields (PK/FK, business keys), cardinalities.
- Deep: all fields with types, nullability, constraints, indexes, enum values, where each entity is read/written.

**API / interface spec**
- Overview: list of interfaces (name, protocol, direction, consumer/provider).
- Standard: every operation with method/path or topic, purpose, request/response summary, auth.
- Deep: full field-level request/response/message schemas, status/error codes, examples, versioning, rate limits.
