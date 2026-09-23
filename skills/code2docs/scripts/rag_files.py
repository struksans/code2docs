#!/usr/bin/env python3
"""Search a RAG index exported to files, for code2docs.

Loads chunks from *.json, *.jsonl, *.md, *.markdown, *.txt under a folder and
runs keyword (BM25-like) or regex search. Standard library only (Python 3.8+).

Usage:
    python3 rag_files.py <folder> --sources
    python3 rag_files.py <folder> --query "kafka topic orders" [-k 10]
    python3 rag_files.py <folder> --regex "POST\\s+/\\w+"
    python3 rag_files.py <folder> --query "..." --out results.json
Custom field names (dot paths allowed):
    --text-field page_content --source-field metadata.file --id-field metadata.chunk_id
"""

import argparse
import json
import math
import os
import re
import sys
from collections import Counter

TEXT_FIELDS = ["text", "content", "page_content", "chunk", "document", "body", "pageContent"]
SOURCE_FIELDS = ["source", "metadata.source", "metadata.file_path", "metadata.filename",
                 "metadata.path", "metadata.url", "path", "file", "url", "title", "metadata.title"]
ID_FIELDS = ["id", "chunk_id", "_id", "metadata.id", "metadata.chunk_id", "uuid"]
LIST_KEYS = ["chunks", "documents", "data", "items", "records", "results", "points"]
TEXT_EXT = (".md", ".markdown", ".txt", ".rst")
TOKEN = re.compile(r"[A-Za-z0-9_]+")
MD_HEADING = re.compile(r"^(#{1,6})\s+(.*)")
MAX_TEXT_CHUNK = 4000


def dig(obj, path):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def first(obj, paths):
    for p in paths:
        v = dig(obj, p)
        if v not in (None, "", [], {}):
            return v
    return None


def records_from_json(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in LIST_KEYS:
            if isinstance(data.get(k), list):
                return data[k]
        # Chroma-style: {"ids": [...], "documents": [...], "metadatas": [...]}
        if isinstance(data.get("ids"), list) and isinstance(data.get("documents"), list):
            metas = data.get("metadatas") or [{}] * len(data["ids"])
            return [{"id": i, "text": d, "metadata": m or {}} for i, d, m in zip(data["ids"], data["documents"], metas)]
        return [data]
    return []


def split_text_file(rel, text):
    """Split md/txt into chunks at headings (md) or blank-line paragraphs."""
    chunks, buf, heading, start = [], [], "", 1
    lines = text.splitlines()

    def flush(end_line):
        body = "\n".join(buf).strip()
        if body:
            chunks.append({"id": "%s:%d" % (rel, start), "source": rel,
                           "section": heading, "line": start, "text": body[:MAX_TEXT_CHUNK]})

    for i, line in enumerate(lines, 1):
        m = MD_HEADING.match(line)
        size = sum(len(b) for b in buf)
        if m or size > MAX_TEXT_CHUNK:
            flush(i - 1)
            buf, start = [], i
            if m:
                heading = m.group(2).strip()
        buf.append(line)
    flush(len(lines))
    return chunks


def load(folder, text_fields, source_fields, id_fields):
    chunks, errors = [], []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, folder).replace(os.sep, "/")
            low = fn.lower()
            try:
                if low.endswith(".jsonl") or low.endswith(".ndjson"):
                    with open(full, encoding="utf-8", errors="replace") as fh:
                        recs = [json.loads(l) for l in fh if l.strip()]
                elif low.endswith(".json"):
                    with open(full, encoding="utf-8", errors="replace") as fh:
                        recs = records_from_json(json.load(fh))
                elif low.endswith(TEXT_EXT):
                    with open(full, encoding="utf-8", errors="replace") as fh:
                        chunks.extend(split_text_file(rel, fh.read()))
                    continue
                else:
                    continue
            except (OSError, ValueError) as exc:
                errors.append("%s: %s" % (rel, exc))
                continue
            for n, rec in enumerate(recs):
                if isinstance(rec, str):
                    rec = {"text": rec}
                if not isinstance(rec, dict):
                    continue
                text = first(rec, text_fields)
                if not isinstance(text, str):
                    continue
                src = first(rec, source_fields)
                cid = first(rec, id_fields)
                chunks.append({
                    "id": str(cid) if cid is not None else "%s#%d" % (rel, n),
                    "source": str(src) if src is not None else rel,
                    "section": str(dig(rec, "metadata.section") or dig(rec, "metadata.heading") or ""),
                    "file": rel,
                    "text": text,
                })
    return chunks, errors


def bm25(chunks, query, k):
    terms = [t.lower() for t in TOKEN.findall(query)]
    if not terms:
        return []
    docs = [Counter(t.lower() for t in TOKEN.findall(c["text"])) for c in chunks]
    n = len(docs)
    avg = (sum(sum(d.values()) for d in docs) / n) if n else 1
    df = Counter(t for d in docs for t in set(terms) if t in d)
    scored = []
    for c, d in zip(chunks, docs):
        dl = sum(d.values()) or 1
        s = 0.0
        for t in terms:
            if t in d:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * d[t] * 2.2 / (d[t] + 1.2 * (0.25 + 0.75 * dl / avg))
        if s > 0:
            scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    return [dict(c, score=round(s, 3)) for s, c in scored[:k]]


def regex_search(chunks, pattern, k):
    rx = re.compile(pattern, re.I | re.M)
    out = []
    for c in chunks:
        hits = rx.findall(c["text"])
        if hits:
            out.append(dict(c, score=len(hits)))
    out.sort(key=lambda x: -x["score"])
    return out[:k]


def excerpt(text, query, width=300):
    terms = [t.lower() for t in TOKEN.findall(query or "")]
    low = text.lower()
    pos = min([low.find(t) for t in terms if low.find(t) >= 0] or [0])
    start = max(0, pos - width // 3)
    snippet = text[start:start + width].replace("\n", " ")
    return ("..." if start else "") + snippet + ("..." if start + width < len(text) else "")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Search a RAG index exported to files.")
    ap.add_argument("folder")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--sources", action="store_true", help="list source documents and chunk counts")
    g.add_argument("--query", help="keyword query (BM25-style scoring)")
    g.add_argument("--regex", help="regular expression (case-insensitive)")
    ap.add_argument("-k", "--top-k", type=int, default=10)
    ap.add_argument("--full", action="store_true", help="return full chunk text instead of excerpts")
    ap.add_argument("--text-field", action="append", help="custom text field (dot path)")
    ap.add_argument("--source-field", action="append", help="custom source field (dot path)")
    ap.add_argument("--id-field", action="append", help="custom id field (dot path)")
    ap.add_argument("--out", help="write JSON here (default: stdout)")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.folder):
        ap.error("not a directory: %s" % args.folder)
    chunks, errors = load(args.folder,
                          (args.text_field or []) + TEXT_FIELDS,
                          (args.source_field or []) + SOURCE_FIELDS,
                          (args.id_field or []) + ID_FIELDS)

    if args.sources:
        counts = Counter(c["source"] for c in chunks)
        result = {"folder": os.path.abspath(args.folder), "chunks": len(chunks),
                  "sources": [{"source": s, "chunks": n} for s, n in counts.most_common()],
                  "errors": errors}
    else:
        hits = bm25(chunks, args.query, args.top_k) if args.query else regex_search(chunks, args.regex, args.top_k)
        for h in hits:
            if not args.full:
                h["text"] = excerpt(h["text"], args.query or "")
            h["cite"] = "[rag:%s]" % (h["id"] if h.get("id") else h["source"])
        result = {"query": args.query or args.regex, "mode": "keyword" if args.query else "regex",
                  "chunks_searched": len(chunks), "hits": hits, "errors": errors}

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("Wrote %s" % args.out)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
