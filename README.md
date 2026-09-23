# code2docs

Agent Skills for **Claude Code** and **GitHub Copilot** that generate product and architecture documentation from a **code repository** or a **RAG index**:

- product specification
- application inputs / outputs inventory
- data flow diagrams (DFD level 0/1/2)
- block diagrams (C4 context / container / component)
- sequence diagrams
- data model / ERD
- API / interface specification

Diagrams are produced as **Mermaid**, **PlantUML** (C4-PlantUML) and/or **draw.io**.

Before doing any work the skill **interviews you**: which documents, what detail level (Overview / Standard / Deep), where the source is (code path, RAG via an MCP tool, RAG exported to files), which diagram notation(s), and where to write the output.

## Skills

| Skill | Role |
|---|---|
| `code2docs` | Entry point: interview, run brief, evidence gathering, dispatch, index |
| `code2docs-io-inventory` | Inputs/outputs inventory |
| `code2docs-data-model` | Data model / ERD |
| `code2docs-api-spec` | API / interface spec |
| `code2docs-block-diagram` | C4 block diagrams |
| `code2docs-data-flow` | Data flow diagrams |
| `code2docs-sequence` | Sequence diagrams |
| `code2docs-product-spec` | Product specification |

Sub-skills can also be used on their own; they reuse the settings in `code2docs-brief.md` if it exists, or ask a short set of questions.

## Install

Copy **all** folders from `skills/` together (sub-skills reference `../code2docs/`):

| Tool | Scope | Location |
|---|---|---|
| Claude Code | project | `<repo>/.claude/skills/` |
| Claude Code | personal | `~/.claude/skills/` |
| GitHub Copilot (VS Code agent mode, Copilot CLI, coding agent) | project | `<repo>/.github/skills/` (Copilot also reads `.claude/skills/`) |
| GitHub Copilot | personal | `~/.copilot/skills/` |

```bash
# example: personal install for Claude Code
mkdir -p ~/.claude/skills && cp -r skills/* ~/.claude/skills/
```

In VS Code make sure agent skills are enabled (`chat.useAgentSkills`) if your version still has that setting.

## Use

```
/code2docs                                  # Claude Code slash command
Document the repo in ./services/orders: data flow and block diagram, standard detail
Build a product spec from our RAG index (MCP tool "kb_search"), overview level, output to docs/spec
```

Output (in the directory you choose):

```
code2docs-brief.md        settings of the run (edit & re-run a sub-skill to regenerate)
README.md                 index + open questions
io-inventory.md  data-model.md  api-spec.md  block-diagram.md  data-flow.md  sequences.md  product-spec.md
*.puml  *.drawio          when PlantUML / draw.io were selected
.code2docs/               evidence: inventory.json, RAG hits
```

Every statement cites evidence (`path:line` or `[rag:<chunk>]`); anything not directly supported is marked *(inferred)* or listed under Open questions.

## Helper scripts (optional, Python 3.8+, no dependencies)

Used automatically when Python is available; otherwise the skill falls back to grep/read patterns in `skills/code2docs/references/scan-fallback.md`.

```bash
python3 skills/code2docs/scripts/scan_repo.py <repo> --out out/.code2docs/inventory.json
python3 skills/code2docs/scripts/rag_files.py <rag-folder> --sources
python3 skills/code2docs/scripts/rag_files.py <rag-folder> --query "kafka topics" -k 10
```

`rag_files.py` reads `*.json` / `*.jsonl` (LangChain, LlamaIndex, Chroma exports and similar), `*.md`, `*.txt`.
