# code2docs run brief

> Written by the `code2docs` skill. Sub-skills read this file. Edit it and re-run a sub-skill to regenerate a single document with different settings.

| Setting | Value |
|---|---|
| System name | <name> |
| One-line description | <text> |
| Documents | <product-spec, io-inventory, data-flow, block-diagram, sequence, data-model, api-spec> |
| Detail level | <Overview \| Standard \| Deep> |
| Source type | <code \| rag-mcp \| rag-files> (one or more) |
| Code path(s) | <path, path> |
| Include / exclude globs | <include> / <exclude> |
| Focus areas | <modules, features or "none"> |
| RAG MCP tool | <server/tool name + extra params, or "n/a"> |
| RAG files folder | <path + format + custom field names, or "n/a"> |
| Diagram notation(s) | <mermaid, plantuml, drawio> |
| Output directory | <path> |
| Audience | <business \| architects \| developers \| auditors> |
| Document language | <English> |
| Python available | <yes (command) \| no> |
| Date | <YYYY-MM-DD> |

## Evidence files

- `.code2docs/inventory.json` or `.code2docs/inventory.md` — code scan
- `.code2docs/rag-evidence.md` / `.code2docs/rag-*.json` — RAG results

## Notes from the interview

<anything the user said that affects scope, terminology or emphasis>
