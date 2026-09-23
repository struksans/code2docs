---
name: code2docs-api-spec
description: Document the API / interface specification of an application - REST, GraphQL, gRPC, WebSocket endpoints, published and consumed messages/events, file interfaces - with operations, request/response schemas, auth, errors, from code, existing OpenAPI/proto/AsyncAPI files or a RAG index. Use when the user asks for an API spec, interface spec, endpoint list, contract documentation or integration spec. Part of the code2docs skill family.
---

# API / interface specification

Output: `<output>/api-spec.md` (and, at Deep level if the user wants it, a generated `openapi.yaml` draft marked as reverse-engineered).

## 0. Setup

Same as every code2docs sub-skill: read `code2docs-brief.md` from the output directory; if missing, ask for source + location, detail level, notation(s), output directory, create the brief (`../code2docs/templates/brief.md`) and gather evidence (`../code2docs/SKILL.md` step 3). Follow `../code2docs/references/detail-levels.md`, `sources.md`, `notations.md`.

## 1. Collect

1. **Existing contracts first** (inventory `contracts`): OpenAPI/Swagger, WSDL/XSD (SOAP web services), AsyncAPI, `.proto`, GraphQL SDL, Avro, JSON Schema. If a contract exists, summarise it and link to it; verify against code and note differences.
2. **Provided interfaces** (this app is the server/producer): `http_routes`, GraphQL resolvers, gRPC services, WebSocket handlers, topics it publishes, files it exports.
3. **Consumed interfaces** (this app is the client/consumer): `http_clients`, topics it consumes, files it imports.
4. For each operation open the handler and find: path/topic, method, path/query/header params, request body type, response type(s) and status codes, auth (middleware, decorators, `[Authorize]`, `@PreAuthorize`, API keys), validation, idempotency, pagination, errors raised.
5. Reuse `io-inventory.md` and `data-model.md` if already generated (link, don't duplicate schemas).

## 2. Write `api-spec.md`

```markdown
# <System> — API and interface specification
Source · Level · Date

## Summary                 <interfaces provided / consumed, protocols, auth model, base URLs if known>
## Interface catalogue
| Interface | Type | Role (provides/consumes) | Counterpart | Auth | Contract file | Evidence |
## Provided interfaces
### <Interface name> (REST)
| Method | Path | Purpose | Auth | Request | Response | Errors | Evidence |
#### <METHOD path>             (Deep: one section per operation)
Parameters table · Request schema · Response schema(s) · Error codes · Example (only if found in code/tests/RAG, otherwise mark as illustrative)
### <Service name> (SOAP web service)
| Operation | SOAP action | Input message / elements | Output message | Faults | Auth (WS-Security, basic, mTLS) | Evidence |
### <Topic / queue> (messaging)
| Topic | Direction | Message type | Key | Schema | Delivery semantics | Evidence |
## Consumed interfaces      (same structure; include timeouts/retries if found)
## Cross-cutting             auth, versioning, pagination, error format, rate limits, correlation IDs
## Open questions
```

Level specifics:
- **Overview**: catalogue table only + cross-cutting summary.
- **Standard**: one row per operation/topic with request/response type names.
- **Deep**: field-level schemas (name, type, required, constraints, description), status codes, examples, per-operation evidence.

## 3. Diagram (optional)

At Standard/Deep include one interface overview diagram: the system with provided interfaces (lollipops / labelled edges from consumers) and consumed interfaces (edges to providers), in the selected notation(s).

## 4. Check

- [ ] Every operation has evidence; contract-vs-code differences listed.
- [ ] Auth documented for each provided interface (or "none found").
- [ ] Schemas reference `data-model.md` entities where they match.
