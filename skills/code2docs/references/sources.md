# Sources and evidence

All evidence goes into `<output>/.code2docs/`. Documents cite it; they never rely on memory or assumptions.

## Evidence format

| Source | Citation format | Example |
|---|---|---|
| Code | `path:line` (path relative to repo root) | `src/api/orders.py:42` |
| RAG chunk | `[rag:<chunk-id>]` or `[rag:<source>#<section>]` | `[rag:confluence/ordering.md#payment]` |
| Inferred | *(inferred)* + short reason | *(inferred — naming convention of `*Consumer` classes)* |

## 1. Code repository

1. Read top-level files first: README, manifests (`package.json`, `pyproject.toml`, `requirements*.txt`, `pom.xml`, `build.gradle*`, `go.mod`, `*.csproj`, `Cargo.toml`, `composer.json`, `Gemfile`), `Dockerfile*`, `docker-compose*.yml`, Helm/K8s manifests, CI files, `.env.example`.
2. Run `scripts/scan_repo.py` (or `scan-fallback.md` without Python).
3. Open entry points and the files that the inventory shows as dense in routes / DB / messaging; follow calls one or two levels deep to understand flows.
4. Existing specs are primary evidence for contracts: OpenAPI/Swagger, `.proto`, GraphQL schema, AsyncAPI, SQL migrations, JSON Schema, Avro.
5. For large repos (> ~2,000 files) at Deep level, ask the user to pick modules first, and process module by module.

Scan output shape (`inventory.json`):

```json
{
  "root": "/abs/path",
  "summary": {"files_scanned": 0, "languages": {"python": 12}},
  "manifests": [{"file": "pyproject.toml", "kind": "python"}],
  "findings": {
    "http_routes":   [{"kind": "flask", "name": "GET /orders", "file": "app.py", "line": 10, "snippet": "..."}],
    "entrypoints":   [], "cli_args": [], "env_vars": [], "file_io": [],
    "databases":     [], "orm_models": [], "messaging": [], "http_clients": [],
    "schedulers":    [], "ui_routes": [], "contracts": []
  }
}
```

## 2. RAG via MCP tool

The user names the tool. Run each query below (adapt wording to the domain; add the system name). Use top-k 5–10; at Deep level repeat with narrower follow-up queries for every component found.

Query plan:

1. `<system> overview purpose business goal`
2. `users roles personas permissions`
3. `features functionality use cases`
4. `architecture components services modules`
5. `external systems integrations third party API`
6. `REST endpoints API operations requests responses`
7. `events messages queues topics kafka`
8. `database tables entities data model schema`
9. `input files import upload batch`
10. `output reports export notifications email`
11. `configuration environment variables settings`
12. `authentication authorization security`
13. `errors failure handling retries`
14. `non-functional performance availability scaling`
15. `deployment infrastructure environments`

Record for each hit: chunk id (or the tool's reference field), source document, 1–3 line excerpt, which query found it. Deduplicate by chunk id. Write to `.code2docs/rag-evidence.md` grouped by query.

If the tool returns code chunks, treat their file paths like code citations but prefix with `rag:`.

## 3. RAG files on disk

Supported: `*.json` (array of objects or `{"chunks": [...]}`), `*.jsonl`, `*.md`, `*.txt`. Text field auto-detected from `text`, `content`, `page_content`, `chunk`, `document`; source from `source`, `metadata.source`, `metadata.file_path`, `path`, `url`, `title`; id from `id`, `chunk_id`, `metadata.id`.

```
python3 scripts/rag_files.py <folder> --sources                    # what documents exist
python3 scripts/rag_files.py <folder> --query "kafka topic" -k 10  # keyword search (all terms scored)
python3 scripts/rag_files.py <folder> --regex "POST\s+/\w+"        # regex search
python3 scripts/rag_files.py <folder> --query "..." --out <output>/.code2docs/rag-q06.json
```

Custom field names: `--text-field`, `--source-field`, `--id-field` (dot paths allowed, e.g. `metadata.src`).

Without Python: list the folder, grep for the query terms (case-insensitive), open matching files.

## 4. Code + RAG together

- Code wins for *what the system does*; RAG wins for *why* and business vocabulary.
- If RAG describes something not found in code: list under **Open questions** as "documented but not found in code".
- If code does something RAG never mentions: document it from code, mark *(undocumented)*.
