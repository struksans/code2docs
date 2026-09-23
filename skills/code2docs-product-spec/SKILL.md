---
name: code2docs-product-spec
description: Write a product specification for an existing application reverse-engineered from its code repository and/or RAG index - purpose, users and roles, features, functional requirements, business rules, non-functional characteristics, integrations, constraints and open questions - with traceability to code/RAG evidence. Use when the user asks for a product spec, PRD, functional specification, requirements document or "what does this system do" write-up. Part of the code2docs skill family.
---

# Product specification

Output: `<output>/product-spec.md`.

## 0. Setup

Same as every code2docs sub-skill: read `code2docs-brief.md` from the output directory; if missing, ask for source + location, detail level, notation(s), output directory, create the brief (`../code2docs/templates/brief.md`) and gather evidence (`../code2docs/SKILL.md` step 3). Follow `../code2docs/references/detail-levels.md`, `sources.md`, `notations.md`.

This document is written last in a full run: link to and summarise the other generated documents instead of repeating them.

## 1. Collect

- **Purpose & scope**: README, package descriptions, RAG queries 1 and 3, UI titles, domain names in code.
- **Users & roles**: auth roles/claims/scopes, permission checks, UI routes per role, RAG query 2.
- **Features**: group endpoints/UI routes/jobs/consumers by domain concept (folder, controller, bounded context). Each feature = a user-visible capability.
- **Business rules**: validation logic, state machines/status enums, calculations, limits, feature flags. Read the service layer, not just controllers.
- **Non-functional (observed only)**: authN/authZ, encryption/TLS, logging/monitoring/tracing, caching, retries/timeouts, rate limiting, scaling config (replicas, workers), i18n, accessibility hints, data retention jobs.
- **Integrations & constraints**: from io-inventory/api-spec; technology stack from manifests; deployment environment.

## 2. Write `product-spec.md`

```markdown
# <System> — Product specification
Source · Level · Date · Status: reverse-engineered draft

## 1. Overview            purpose, problem solved, scope / out of scope
## 2. Users and roles     | Role | Description | Main capabilities | Evidence |
## 3. Features            | ID | Feature | Description | Roles | Evidence |
## 4. Functional requirements
| ID | Requirement ("The system shall …") | Feature | Priority* | Evidence |
   (*priority only if RAG/docs state it; otherwise omit the column)
### Business rules        (Standard/Deep) | ID | Rule | Applies to | Evidence |
## 5. Non-functional characteristics (observed)
| Area | Observation | Evidence |
## 6. Integrations        summary + link to io-inventory.md / api-spec.md
## 7. Data                summary + link to data-model.md
## 8. Architecture        summary + link to block-diagram.md, data-flow.md, sequences.md
## 9. Constraints and assumptions   tech stack, platform, regulatory hints
## 10. Traceability       (Deep) | Requirement | Code locations | RAG sources | Tests |
## 11. Open questions / gaps        documented-but-not-implemented, implemented-but-undocumented, unclear behaviour
```

Level specifics:
- **Overview**: sections 1–3, 6, 11; max ~10 features; plain language for business readers.
- **Standard**: all sections except 10; FRs per feature; business rules for core flows.
- **Deep**: all sections; acceptance-style detail per FR (inputs, validation, outcomes, error cases); full traceability.

Write requirements in the brief's document language, business vocabulary from RAG where available. Never present guesses as requirements: *(inferred)* items go to a separate "Candidate requirements" list or Open questions.

## 3. Check

- [ ] Every feature and FR has evidence.
- [ ] Roles match the auth code.
- [ ] Links to other generated documents work (relative paths).
- [ ] Open questions list conflicts between code and RAG.
