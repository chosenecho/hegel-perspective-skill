"""Bounded offline lookup and integrity checks for the archived Hegel corpus.

No network or agent framework required. Hash verification checks file integrity,
not authorship, editorial fidelity, philosophical truth, or reading completeness.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "references/sources/manifest.json"

def normalize(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text).replace("_", "")).strip()

def read_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8-sig"))

def safe_path(relative):
    p = (ROOT / relative).resolve()
    if not p.is_relative_to(ROOT.resolve()):
        raise ValueError("archive path leaves the skill directory")
    return p

def output(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


class ParagraphReader(HTMLParser):
    """Keep inline text adjacent; do not insert spaces around emphasis tags."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.paragraphs = []

    def finish(self):
        if self.current is not None:
            text = re.sub(r"\s+", " ", "".join(self.current)).strip()
            if text:
                self.paragraphs.append(text)
            self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.finish()
            self.current = []
        elif tag == "br" and self.current is not None:
            self.current.append(" ")

    def handle_endtag(self, tag):
        if tag == "p":
            self.finish()

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)


def quote_paragraphs(row, query):
    raw = safe_path(row["raw_path"])
    if raw.suffix.lower() != ".html":
        raise ValueError("quote supports archived HTML p-elements; read raw TXT/PDF directly")
    parser = ParagraphReader()
    parser.feed(raw.read_bytes().decode(row.get("encoding", "utf-8"), errors="strict"))
    parser.finish()
    needle = re.sub(r"\s+", " ", query).casefold()
    return [p for p in parser.paragraphs if needle in p.casefold()]

def audit(rows):
    errors = []
    for r in rows:
        if r.get("status") != "ok":
            errors.append({"id":r["id"], "problem":r.get("error", "not archived")})
            continue
        raw = safe_path(r["raw_path"])
        if not raw.is_file(): errors.append({"id":r["id"], "problem":"missing raw file"}); continue
        if hashlib.sha256(raw.read_bytes()).hexdigest() != r["sha256"]:
            errors.append({"id":r["id"], "problem":"raw SHA-256 mismatch"})
        if r.get("text_path") and not safe_path(r["text_path"]).is_file():
            errors.append({"id":r["id"], "problem":"missing extracted text"})
    return {"resources":len(rows), "raw_bytes":sum(r.get("bytes",0) for r in rows),
            "distinct_work_labels":len({r["work"] for r in rows}),
            "status":"PASS" if not errors else "FAIL", "errors":errors,
            "scope":"File integrity only. Pages, works, and independent sources are different units."}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("find"); p.add_argument("query"); p.add_argument("--limit",type=int,default=8)
    p.add_argument("--id",help="optional source ID prefix")
    p = sub.add_parser("show"); p.add_argument("id"); p.add_argument("--find",required=True)
    p.add_argument("--context",type=int,default=650)
    p = sub.add_parser("quote", help="read raw HTML paragraph text, preserving inline punctuation")
    p.add_argument("id"); p.add_argument("--find", required=True)
    sub.add_parser("audit")
    args = ap.parse_args()
    rows = read_manifest()
    if args.command == "audit":
        result = audit(rows); output(result); return 0 if result["status"]=="PASS" else 1
    if args.command in {"show", "quote"}:
        matches = [r for r in rows if r["id"]==args.id]
        if len(matches)!=1: ap.error("unknown or ambiguous source ID")
        r = matches[0]
        if args.command == "quote":
            try:
                paragraphs = quote_paragraphs(r, args.find)
            except (OSError, ValueError, UnicodeError) as exc:
                ap.error(str(exc))
            output({"id": r["id"], "url": r.get("url", r["requested_url"]),
                    "raw_path": r["raw_path"], "raw_sha256": r["sha256"], "whole_file_grade": r["grade"], "matches": len(paragraphs),
                    "paragraphs": [p[:4000] for p in paragraphs[:3]],
                    "truncated": any(len(p) > 4000 for p in paragraphs[:3]),
                    "scope": "Raw HTML paragraph text with layout whitespace collapsed. Verify locator/editorial layer; not a facsimile collation."})
            return 0 if paragraphs else 1
        if not r.get("text_path"): ap.error("PDF has no extracted text in this manifest; use a PDF reader")
        txt = normalize(safe_path(r["text_path"]).read_text(encoding="utf-8"))
        needle = normalize(args.find)
        found = list(re.finditer(re.escape(needle), txt, re.I))
        size = min(max(args.context,80),2400)
        output({"id":r["id"],"url":r.get("url",r["requested_url"]),"grade":r["grade"],
                "work":r["work"],"matches":len(found),
                "excerpts":[txt[max(0,m.start()-size//3):m.end()+size] for m in found[:3]]})
        return 0 if found else 1
    needle = normalize(args.query).casefold()
    results = []
    for r in rows:
        if args.id and not r["id"].startswith(args.id): continue
        if not r.get("text_path"): continue
        txt = normalize(safe_path(r["text_path"]).read_text(encoding="utf-8"))
        i = txt.casefold().find(needle)
        if i >= 0:
            results.append({"id":r["id"], "work":r["work"], "grade":r["grade"],
                            "url":r.get("url",r["requested_url"]),
                            "excerpt":txt[max(0,i-100):i+len(needle)+350]})
    output({"query":args.query,"matching_files":len(results),"results":results[:min(max(args.limit,1),30)]})
    return 0 if results else 1

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
