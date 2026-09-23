---
name: code2docs
description: Generate product specifications and architecture documentation from a code repository or a RAG index - product spec, application inputs/outputs inventory, data flow diagrams, block/C4 diagrams, sequence diagrams, data model/ERD and API/interface specs, as Mermaid, PlantUML or draw.io. Use when the user asks to document, reverse-engineer, spec out or diagram an existing system, codebase, repo or RAG/vector index ("spec from code", "what are the inputs and outputs", "draw the data flow", "architecture diagram of this repo"). Interviews the user first about which documents, detail level, source location and output path.
---

# code2docs — documentation from code or a RAG index

You are the entry point of the code2docs skill family. You **interview the user**, **gather evidence** from the chosen source, then produce each requested document by following the matching sub-skill.

Sibling skills (must be installed next to this folder):

| Document | Skill folder | Output file |
|---|---|---|
| Inputs / outputs inventory | `../code2docs-io-inventory/` | `io-inventory.md` |
| Data model / ERD | `../code2docs-data-model/` | `data-model.md` |
| API / interface spec | `../code2docs-api-spec/` | `api-spec.md` |
| Block diagram (C4) | `../code2docs-block-diagram/` | `block-diagram.md` |
| Data flow (DFD) | `../code2docs-data-flow/` | `data-flow.md` |
| Sequence diagrams | `../code2docs-sequence/` | `sequences.md` |
| Product specification | `../code2docs-product-spec/` | `product-spec.md` |

Paths below are relative to this skill's folder (`code2docs/`).

## Step 1 — Interview (never skip)

Follow `references/interview.md`. Summary:

- Ask in rounds of at most 4 questions. Use a structured question tool if your agent has one (e.g. `AskUserQuestion`); otherwise ask in chat as a numbered list with the options shown, and **stop and wait** for the answer.
- Do not re-ask anything the user already stated in the request.
- Required answers before any scanning starts:
  1. **Documents** — which of the 7 types (or "full pack").
  2. **Detail level** — Overview / Standard / Deep (see `references/detail-levels.md`).
  3. **Source** — code repository path(s), RAG via MCP tool, RAG files on disk, or a combination — plus the concrete location (path, MCP tool name, folder).
  4. **Diagram notation(s)** — Mermaid, PlantUML (C4-PlantUML for block diagrams), draw.io; one or several.
  5. **Output directory** — where to write the files.
- Optional (use defaults if the user skips): system name, audience, document language, focus areas / exclusions.
- Finish with a short summary of all answers and ask for confirmation.

## Step 2 — Write the run brief

Copy `templates/brief.md` to `<output>/code2docs-brief.md` and fill it with the answers. Every sub-skill reads this file, so a sub-skill can later be re-run alone with the same settings.

## Step 3 — Gather evidence

Follow `references/sources.md`. Write all evidence to `<output>/.code2docs/`.

- **Code repository**
  - Check Python: run `python3 --version` (on Windows also try `python --version` / `py --version`).
  - If available: `python3 <this-skill-dir>/scripts/scan_repo.py <repo> --out <output>/.code2docs/inventory.json` (add `--include`/`--exclude` globs from the brief). Then read the JSON and open the most relevant files to confirm and deepen findings — the scan is a starting point, not the answer.
  - If not available: follow `references/scan-fallback.md` and write `<output>/.code2docs/inventory.md` by hand using the same categories.
- **RAG via MCP tool** — run the query plan in `references/sources.md` with the tool the user named. Save results (chunk id, source, short excerpt) to `<output>/.code2docs/rag-evidence.md`.
- **RAG files on disk** — with Python: `python3 <this-skill-dir>/scripts/rag_files.py <folder> --sources` to see what is there, then `--query "<terms>"` for each query in the plan, `--out` into `.code2docs/`. Without Python: grep/read the folder following the same query plan.
- **Both code and RAG** — code is the source of truth for behaviour; RAG adds intent, business terms and requirements. Record conflicts as open questions.

At Standard and Deep level, show the user a 5–10 line summary of what was found (components, external systems, entry points) and ask whether anything important is missing before writing documents.

## Step 4 — Produce the documents

For each selected document, read the sibling `SKILL.md` and follow it. Order (later docs reuse earlier ones):

io-inventory → data-model → api-spec → block-diagram → data-flow → sequence → product-spec

If your agent can run subagents, documents after `io-inventory` may be produced in parallel — give each subagent the brief path and the evidence folder.

Diagram rules for all documents are in `references/notations.md`. For draw.io start from `templates/drawio-skeleton.drawio`.

## Step 5 — Index and hand-off

Write `<output>/README.md`:
- system name, date, source, detail level;
- links to every generated file;
- consolidated **Open questions** and **Low-confidence items** (collected from each document).

Tell the user where the files are and list the top open questions.

## Ground rules (apply to every document)

- Every fact needs evidence: `path/to/file.ext:line` for code, `[rag:<chunk-id or source>]` for RAG. At Deep level every table row carries a citation.
- Mark anything not directly supported as *(inferred)*. Never invent components, endpoints, tables or integrations.
- A diagram may only contain elements that appear in the evidence or in the document text.
- Prefer names used in the code/RAG; add a plain-language description next to technical names.
- Do not copy secrets: if a config value looks like a credential, write `<redacted>`.
