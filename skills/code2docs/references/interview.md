# Interview script

Goal: collect everything needed to produce the documents **before** reading the source. Ask in rounds (max 4 questions per round). Skip any question already answered by the user's request. Offer the listed options; the user can always answer free-form.

## Round 1 — What and how deep

**Q1. Which documents do you need?** (multi-select)
- Product specification — purpose, users, features, functional/non-functional requirements
- Inputs / outputs inventory — every way data enters and leaves the application
- Data flow diagram — how data moves between actors, processes and stores
- Block diagram — system / containers / components (C4 style)
- Sequence diagrams — key use cases step by step
- Data model / ERD — entities, fields, relations
- API / interface spec — endpoints, messages, contracts
- Full pack — all of the above
- Backlog — epics, features and user stories for re-implementing the application elsewhere (needs product spec, I/O inventory, data model and API spec; Deep level recommended)

**Q2. What level of detail?**
- Overview — for stakeholders; context level, 1 diagram per document, ~1–2 pages each
- Standard — for architects/new developers; modules/containers, all external interfaces, main flows *(default)*
- Deep — for engineers/audit; per-component, every input/output with file:line, field-level schemas, error paths

**Q3. Where is the source?** (multi-select)
- Code repository on disk
- RAG index through an MCP tool
- RAG index exported as files on disk (json / jsonl / md / txt)

**Q4. Which diagram notation(s)?** (multi-select)
- Mermaid — renders in GitHub, GitLab, VS Code, Confluence plugins *(default)*
- PlantUML (C4-PlantUML for block diagrams)
- draw.io (`.drawio` files editable in diagrams.net / VS Code extension)

## Round 2 — Source details (ask only what applies)

- **Code**: path(s) to the repository or sub-folders? Anything to exclude (tests, generated code, vendored libs)? Any module or feature to focus on?
- **RAG via MCP**: which MCP server / tool should be used for retrieval? Before asking, list the tools you can see whose names or descriptions suggest search/retrieve/query and offer them as options. Also ask whether the tool needs extra parameters (index/collection name, filters, top-k).
- **RAG files**: folder path? File format if known? Which field holds the text / the source reference, if non-standard?
- **System name** and short description (one line) if not obvious.

## Round 3 — Output

- **Output directory** — where to write files? (Suggest `docs/code2docs/` inside the repo, or a sibling folder when the source is read-only.) Warn if the folder already contains files with the same names and ask: overwrite, write next to them with a suffix, or choose another folder.
- **Audience** (optional) — business, architects, developers, auditors. Influences wording, not facts.
- **Document language** (optional) — default: the language the user writes in.

## Confirmation

Print a summary and ask "Proceed?":

```
System:        <name>
Documents:     <list>
Detail level:  <level>
Source:        <code path(s) / MCP tool / RAG folder>
Scope:         include <...> exclude <...> focus <...>
Notation(s):   <Mermaid | PlantUML | draw.io>
Output dir:    <path>
Audience/lang: <...>
```

## Standalone sub-skill mini-interview

When a sub-skill runs without a brief (`code2docs-brief.md` not found), it asks only: source + location, detail level, notation(s), output directory. It then writes a brief so later runs reuse it.
