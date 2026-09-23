---
name: code2docs-block-diagram
description: Produce block / architecture diagrams in C4 style (system context, containers, components) for an existing application from its code repository or RAG index, rendered as Mermaid, C4-PlantUML or draw.io, with a description of every block and its responsibilities. Use when the user asks for a block diagram, architecture diagram, component diagram, C4 model or system overview. Part of the code2docs skill family.
---

# Block diagram (C4)

Output: `<output>/block-diagram.md` (+ `block-diagram-<level>.puml`, `block-diagram.drawio` with one page per view when selected).

## 0. Setup

Same as every code2docs sub-skill: read `code2docs-brief.md` from the output directory; if missing, ask for source + location, detail level, notation(s), output directory, create the brief (`../code2docs/templates/brief.md`) and gather evidence (`../code2docs/SKILL.md` step 3). Follow `../code2docs/references/detail-levels.md`, `sources.md`, `notations.md`.

## 1. Identify blocks

- **People / actors**: user roles from auth code (roles, scopes, claims), UI routes, RAG "users roles".
- **The system**: name from brief.
- **Containers** (separately deployable/runnable units): each Dockerfile / compose service / K8s deployment / serverless function / frontend app / worker process / CLI; each database, cache, queue broker, object store it owns.
- **Components** (inside a container): top-level packages/modules/namespaces, controllers, services, repositories, consumers, schedulers. Use folder structure + class naming + dependency direction (imports).
- **External systems**: targets of `http_clients`, external brokers/DBs not owned, identity providers, payment/e-mail/SMS providers, other internal systems named in config or RAG.
- **Relations**: who calls whom, with purpose and protocol, from imports, client calls, messaging and DB access.

For monorepos, each app/service folder with its own manifest is a container.

## 2. Views by level

| Level | Views |
|---|---|
| Overview | System Context |
| Standard | System Context + Container |
| Deep | System Context + Container + Component view for each container (+ key class diagram if requested) |

## 3. Write `block-diagram.md`

```markdown
# <System> — Block diagrams
Source · Level · Date

## System context
<diagram>
| Element | Type | Description | Evidence |

## Containers
<diagram>
| Container | Technology | Responsibility | Runs as | Evidence |

## Components — <Container>          (Deep, one section per container)
<diagram>
| Component | Code location | Responsibility | Depends on | Evidence |

## Relations
| From | To | Purpose | Protocol / technology | Sync/async | Evidence |

## Open questions
```

## 4. Diagram rules

- Mermaid: `flowchart LR/TB` with `subgraph` as system/container boundary (or Mermaid `C4Context`/`C4Container` if the user asked for C4 syntax).
- PlantUML: C4-PlantUML (`C4_Context.puml`, `C4_Container.puml`, `C4_Component.puml`) with `Person`, `System`, `System_Ext`, `Container`, `ContainerDb`, `ContainerQueue`, `Component`, `Rel`.
- draw.io: one page per view; boundaries as swimlanes; styles from the skeleton template.
- Include technology in container/component labels at Standard/Deep (`Order API [FastAPI]`).
- Same element names across all views and notations.

## 5. Check

- [ ] Every container maps to something deployable or a data store with evidence.
- [ ] Every external system is backed by a client call, config entry or RAG reference.
- [ ] No orphan elements (each has at least one relation) unless explained.
