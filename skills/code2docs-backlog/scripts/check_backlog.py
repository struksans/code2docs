#!/usr/bin/env python3
"""Validate a code2docs backlog and compute the implementation order.

Reads <backlog>/epics/*.md and <backlog>/gaps.md, finds story headers such as
    ### E01-F02-S03 — Create order
    ### G-01 — Validate e-mail format
and checks:
  errors   duplicate IDs, dependencies on unknown IDs, dependency cycles,
           stories without a Gherkin Scenario
  warnings no user-story statement, empty data mapping, no legacy evidence
Then computes implementation waves (topological levels).

With --spec <dir> it also lists specification items not covered by any story:
FR-ids from product-spec.md, "METHOD /path" operations from api-spec.md and
entity headings from data-model.md. Items listed under "Intentionally out of
scope" in traceability.md count as covered.

Standard library only (Python 3.8+).

Usage:
    python3 check_backlog.py <backlog-dir> [--spec <spec-dir>] [--write-order] [--json]
Exit code 1 when errors are found.
"""

import argparse
import glob
import json
import os
import re
import sys
from collections import OrderedDict

ID = r"(?:[A-Z]+\d+-F\d+-S\d+|G-\d+)"
STORY_HEADER = re.compile(r"^(#{2,4})\s+(" + ID + r")\s+[—–-]+\s+(.+?)\s*$")
ANY_HEADER = re.compile(r"^(#{1,6})\s+")
DEPENDS = re.compile(r"depends\s+on\s*:\s*(.*)", re.I)
ID_RX = re.compile(ID)
SCENARIO = re.compile(r"^\s*Scenario( Outline)?\s*:", re.M)
STATEMENT = re.compile(r"\bAs an?\b.*?\bI want\b", re.I | re.S)
EVIDENCE = re.compile(r"`[^`\s]+:\d+`|\[rag:[^\]]+\]")
NO_MAPPING = re.compile(r"no data mapping", re.I)
MAPPING_HEAD = re.compile(r"data\s*(&|and)\s*interface\s*mapping", re.I)
TABLE_ROW = re.compile(r"^\s*\|(.+)\|\s*$")
FR_RX = re.compile(r"\bFR-\d+\b")
OP_RX = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\b[\s|`*]*(/[\w/{}<>:.\-]*)")
COVERAGE_LABELS = {"functional_requirements": "requirement", "api_operations": "API operation", "entities": "entity"}
ENTITY_HEAD = re.compile(r"^###\s+`?([A-Za-z_][\w ]*?)`?\s*$")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def parse_stories(backlog):
    files = sorted(glob.glob(os.path.join(backlog, "epics", "*.md")))
    gaps = os.path.join(backlog, "gaps.md")
    if os.path.isfile(gaps):
        files.append(gaps)
    stories, duplicates = OrderedDict(), []
    for path in files:
        rel = os.path.relpath(path, backlog).replace(os.sep, "/")
        lines = read(path).splitlines()
        current = None
        for n, line in enumerate(lines, 1):
            m = STORY_HEADER.match(line)
            h = ANY_HEADER.match(line)
            if m or (h and current and len(h.group(1)) <= current["level"]):
                current = None
            if m:
                sid = m.group(2)
                if sid in stories:
                    duplicates.append({"id": sid, "first": stories[sid]["where"], "again": "%s:%d" % (rel, n)})
                    continue
                current = {"id": sid, "title": m.group(3), "where": "%s:%d" % (rel, n),
                           "level": len(m.group(1)), "body": []}
                stories[sid] = current
            elif current is not None:
                current["body"].append(line)
    for s in stories.values():
        s["body"] = "\n".join(s["body"])
        deps = []
        for dm in DEPENDS.finditer(s["body"]):
            deps.extend(ID_RX.findall(dm.group(1)))
        s["depends_on"] = list(OrderedDict.fromkeys(d for d in deps if d != s["id"]))
    return stories, duplicates, files


def mapping_rows(body):
    """Count non-empty data rows of the table following the mapping heading."""
    lines = body.splitlines()
    start = next((i for i, l in enumerate(lines) if MAPPING_HEAD.search(l)), None)
    if start is None:
        return None
    rows = 0
    seen_table = False
    for line in lines[start + 1:]:
        if ANY_HEADER.match(line) or (line.startswith("**") and seen_table):
            break
        m = TABLE_ROW.match(line)
        if not m:
            if seen_table and line.strip():
                break
            continue
        seen_table = True
        cells = [c.strip() for c in m.group(1).split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if cells and cells[0].lower().startswith("legacy source"):
            continue
        if any(cells):
            rows += 1
    return rows


def find_cycle(nodes, edges):
    color, stack = {n: 0 for n in nodes}, []

    def dfs(n):
        color[n] = 1
        stack.append(n)
        for d in edges.get(n, []):
            if d not in color:
                continue
            if color[d] == 1:
                return stack[stack.index(d):] + [d]
            if color[d] == 0:
                c = dfs(d)
                if c:
                    return c
        stack.pop()
        color[n] = 2
        return None

    for n in nodes:
        if color[n] == 0:
            c = dfs(n)
            if c:
                return c
    return None


def waves(stories):
    remaining = {sid: set(d for d in s["depends_on"] if d in stories) for sid, s in stories.items()}
    done, result = set(), []
    while remaining:
        ready = [sid for sid, deps in remaining.items() if deps <= done]
        if not ready:
            break
        result.append(ready)
        done.update(ready)
        for sid in ready:
            del remaining[sid]
    return result, list(remaining)


def coverage(spec, backlog, stories):
    text = "\n".join(s["body"] + "\n" + s["title"] for s in stories.values())
    trace = os.path.join(backlog, "traceability.md")
    if os.path.isfile(trace):
        t = read(trace)
        m = re.search(r"^#+\s*Intentionally out of scope.*?$(.*?)(?=^#\s|^##\s|\Z)", t, re.I | re.M | re.S)
        if m:
            text += "\n" + m.group(1)
    low = text.lower()
    result = {}

    ps = os.path.join(spec, "product-spec.md")
    if os.path.isfile(ps):
        frs = sorted(set(FR_RX.findall(read(ps))), key=lambda x: int(x[3:]))
        result["functional_requirements"] = {"total": len(frs),
                                             "uncovered": [f for f in frs if not re.search(r"\b%s\b" % f, text)]}
    api = os.path.join(spec, "api-spec.md")
    if os.path.isfile(api):
        ops = list(OrderedDict.fromkeys("%s %s" % (m.group(1), m.group(2)) for m in OP_RX.finditer(read(api))))
        found = set("%s %s" % (m.group(1), m.group(2)) for m in OP_RX.finditer(text))
        result["api_operations"] = {"total": len(ops), "uncovered": [o for o in ops if o not in found]}
    dm = os.path.join(spec, "data-model.md")
    if os.path.isfile(dm):
        ents, in_entities = [], False
        for line in read(dm).splitlines():
            if re.match(r"^##\s", line):
                in_entities = bool(re.match(r"^##\s+Entities", line, re.I))
            elif in_entities:
                m = ENTITY_HEAD.match(line)
                if m:
                    ents.append(m.group(1).strip())
        result["entities"] = {"total": len(ents),
                              "uncovered": [e for e in ents if not re.search(r"\b%s\b" % re.escape(e.lower()), low)]}
    return result


def order_markdown(stories, wave_list, stuck):
    out = ["# Implementation order", "",
           "Generated by `check_backlog.py`. Wave *n* depends only on stories in earlier waves; stories within a wave can be built in parallel.", ""]
    for i, w in enumerate(wave_list, 1):
        out.append("## Wave %d" % i)
        out.append("")
        out.append("| Story | Title | Depends on |")
        out.append("|---|---|---|")
        for sid in w:
            s = stories[sid]
            out.append("| %s | %s | %s |" % (sid, s["title"], ", ".join(s["depends_on"]) or "—"))
        out.append("")
    if stuck:
        out += ["## Unordered (dependency cycle)", "", ", ".join(stuck), ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate a code2docs backlog and compute implementation waves.")
    ap.add_argument("backlog", help="backlog directory (contains epics/ and gaps.md)")
    ap.add_argument("--spec", help="specification directory (product-spec.md, api-spec.md, data-model.md)")
    ap.add_argument("--write-order", action="store_true", help="write implementation-order.md into the backlog dir")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = ap.parse_args(argv)
    if not os.path.isdir(args.backlog):
        ap.error("not a directory: %s" % args.backlog)

    stories, duplicates, files = parse_stories(args.backlog)
    errors, warnings = [], []
    if not stories:
        errors.append("no stories found (expected headers like '### E01-F01-S01 — Title' in epics/*.md or gaps.md)")
    for d in duplicates:
        errors.append("duplicate id %s at %s (first at %s)" % (d["id"], d["again"], d["first"]))
    for sid, s in stories.items():
        for dep in s["depends_on"]:
            if dep not in stories:
                errors.append("%s (%s) depends on unknown story %s" % (sid, s["where"], dep))
        if not SCENARIO.search(s["body"]):
            errors.append("%s (%s) has no Gherkin Scenario" % (sid, s["where"]))
        if not STATEMENT.search(s["body"]):
            warnings.append("%s has no 'As a ... I want ...' statement" % sid)
        if not DEPENDS.search(s["body"]):
            warnings.append("%s has no 'Depends on:' line" % sid)
        rows = mapping_rows(s["body"])
        if not NO_MAPPING.search(s["body"]) and not rows:
            warnings.append("%s has an empty data mapping (add rows or write 'No data mapping — <reason>')" % sid)
        if not EVIDENCE.search(s["body"]):
            warnings.append("%s cites no legacy evidence (`path:line` or [rag:...])" % sid)

    edges = {sid: [d for d in s["depends_on"] if d in stories] for sid, s in stories.items()}
    cycle = find_cycle(list(stories), edges)
    if cycle:
        errors.append("dependency cycle: " + " -> ".join(cycle))
    wave_list, stuck = waves(stories)

    cov = coverage(args.spec, args.backlog, stories) if args.spec else {}
    for kind, c in cov.items():
        for item in c["uncovered"]:
            warnings.append("uncovered %s: %s" % (COVERAGE_LABELS.get(kind, kind), item))

    if args.write_order:
        with open(os.path.join(args.backlog, "implementation-order.md"), "w", encoding="utf-8") as fh:
            fh.write(order_markdown(stories, wave_list, stuck) + "\n")

    report = {
        "files": [os.path.relpath(f, args.backlog) for f in files],
        "stories": len(stories),
        "gap_stories": sum(1 for s in stories if s.startswith("G-")),
        "errors": errors, "warnings": warnings,
        "waves": wave_list, "unordered": stuck, "coverage": cov,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("Stories: %d (gap: %d) in %d files" % (report["stories"], report["gap_stories"], len(files)))
        print("Waves: %d%s" % (len(wave_list), " (+%d unordered)" % len(stuck) if stuck else ""))
        for i, w in enumerate(wave_list, 1):
            print("  Wave %d: %s" % (i, ", ".join(w)))
        for kind, c in cov.items():
            print("Coverage %-24s %d/%d" % (kind + ":", c["total"] - len(c["uncovered"]), c["total"]))
        for e in errors:
            print("ERROR   " + e)
        for w in warnings:
            print("WARNING " + w)
        if args.write_order:
            print("Wrote implementation-order.md")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
