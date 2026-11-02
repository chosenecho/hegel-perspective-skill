"""Archive an explicit Hegel research corpus, retaining URLs, bytes and hashes.

Uses publicly served pages; a downloaded file is not evidence that it was read.
Archives are for local research. Site/translation rights remain with owners.
"""
from __future__ import annotations
import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urldefrag, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "references" / "sources"
MANIFEST = DEST / "manifest.json"
BASE = "https://www.marxists.org/reference/archive/hegel/"

# A: author-published; B: correspondence; C: posthumously edited lecture material;
# D: later scholarship/criticism. Mixed files retain a mixed classification.
SEEDS = [
    ("phg-de", "A", "PhG-1807", "https://www.gutenberg.org/ebooks/6698.txt.utf-8", False),
    ("logic1-de", "A", "WdL-I", "https://www.gutenberg.org/ebooks/6729.txt.utf-8", False),
    ("logic2-de", "A", "WdL-II", "https://www.gutenberg.org/ebooks/6834.txt.utf-8", False),
    ("school1809-de", "A", "School-1809", "https://www.gutenberg.org/ebooks/6728.txt.utf-8", False),
    ("enc-logic-pg", "A+C", "Enz-1830-Logic", "https://www.gutenberg.org/ebooks/55108.txt.utf-8", False),
    ("enc-mind-pg", "A+C", "Enz-1830-Mind", "https://www.gutenberg.org/ebooks/39064.txt.utf-8", False),
    ("histphil1-pg", "C", "Lectures-History-Philosophy", "https://www.gutenberg.org/ebooks/51635.txt.utf-8", False),
    ("art1-pg", "C", "Lectures-Aesthetics", "https://www.gutenberg.org/ebooks/55334.txt.utf-8", False),
    ("right", "A+C", "PR-1820-21", BASE + "works/pr/index.htm", True),
    ("logic", "A", "WdL-English-excerpts", BASE + "works/hl/index.htm", True),
    ("shorter", "A+C", "Enz-1830-Logic", BASE + "works/sl/index.htm", True),
    ("phen", "A", "PhG-1807", BASE + "phindex.htm", True),
    ("mind", "A+C", "Enz-1830-Mind", BASE + "works/sp/index-su.htm", True),
    ("objective", "A+C", "Enz-1830-Mind", BASE + "osindex.htm", True),
    ("nature", "A+C", "Enz-1830-Nature", BASE + "natindex.htm", True),
    ("history", "C", "Lectures-History", BASE + "hisindex.htm", True),
    ("religion", "C", "Lectures-Religion", BASE + "reindex.htm", True),
    ("letters", "B", "Letters", BASE + "works/letters/index.htm", True),
    ("abstract", "B", "Who-Thinks-Abstractly", BASE + "works/se/abstract.htm", False),
    ("inaugural", "B", "Berlin-1818", BASE + "works/1818/inaugural.htm", False),
    ("difference", "A", "Difference-1801", BASE + "works/fs/index.htm", True),
    ("faith", "A", "Faith-Knowledge-1802", BASE + "fkindex.htm", True),
    ("education", "D", "Education-Editorial", BASE + "help/hegel-on-education.htm", False),
    ("reform", "A+B", "Reform-1831", BASE + "works/er/english-reform.pdf", False),
    ("sep-hegel", "D", "SEP-Hegel", "https://plato.stanford.edu/entries/hegel/", False),
    ("sep-dialectics", "D", "SEP-Dialectics", "https://plato.stanford.edu/entries/hegel-dialectics/", False),
    ("sep-aesthetics", "D", "SEP-Aesthetics", "https://plato.stanford.edu/entries/hegel-aesthetics/", False),
    ("iep-political", "D", "IEP-Political", "https://iep.utm.edu/hegelsoc/", False),
]

def fetch(task, proxy):
    ident, grade, work, url, crawl = task
    row = dict(id=ident, grade=grade, work=work, requested_url=url,
               retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat(), read_status="archived-not-yet-audited")
    session = requests.Session()
    session.trust_env = False
    session.headers["User-Agent"] = "HegelResearchArchive/2.0 (local scholarly research)"
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        r = session.get(url, proxies=proxies, timeout=(15, 75))
        r.raise_for_status()
        if len(r.content) < 400:
            raise ValueError("response too short to be an archived source")
        is_pdf = r.content.startswith(b"%PDF")
        is_text = ".txt" in r.url or "text/plain" in r.headers.get("Content-Type", "")
        ext = ".pdf" if is_pdf else ".txt" if is_text else ".html"
        raw = DEST / "raw" / (ident + ext)
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(r.content)
        row.update(status="ok", url=r.url, bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest(),
                   content_type=r.headers.get("Content-Type"), raw_path=raw.relative_to(ROOT).as_posix())
        links = []
        if not is_pdf:
            # Honour the HTML declaration instead of requests' ISO-8859-1 default.
            soup = BeautifulSoup(r.content, "html.parser")
            encoding = "utf-8" if is_text else (soup.original_encoding or "utf-8")
            text = r.content.decode(encoding, errors="replace") if is_text else None
            if not is_text:
                for el in soup(["script", "style", "nav"]): el.decompose()
                body = soup.select_one("#main-text") or soup.select_one("#article") or soup.body or soup
                text = body.get_text("\n", strip=True)
                row["anchors"] = list(dict.fromkeys(str(e.get("id") or e.get("name")) for e in soup.select("[id],a[name]")))
                links = list(dict.fromkeys(urldefrag(urljoin(r.url, a["href"]))[0] for a in soup.select("a[href]")))
            clean = DEST / ("articles" if grade == "D" else "books") / (ident + ".txt")
            clean.parent.mkdir(parents=True, exist_ok=True)
            clean.write_text(text, encoding="utf-8")
            row.update(text_path=clean.relative_to(ROOT).as_posix(), characters=len(text), encoding=encoding)
        return row, links
    except Exception as e:
        row.update(status="failed", error=str(e))
        return row, []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proxy", default="", help="optional HTTP proxy; no machine-specific default")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--from-manifest", action="store_true", help="re-fetch every recorded main-corpus URL, including supplementary German witnesses")
    args = ap.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    known = {}
    if MANIFEST.exists():
        known = {r["requested_url"]: r for r in json.loads(MANIFEST.read_text(encoding="utf-8"))}
    if args.from_manifest and not known:
        ap.error("--from-manifest requires an existing manifest.json")
    queue = [(r["id"], r["grade"], r["work"], r["requested_url"], False) for r in known.values()] if args.from_manifest else list(SEEDS)
    seen = set()
    group_prefix = {
        "right": BASE+"works/pr/", "logic": BASE+"works/hl/", "shorter": BASE+"works/sl/",
        "phen": BASE+"works/ph/", "mind": BASE+"works/sp/", "objective": BASE+"works/sp/",
        "nature": BASE+"works/na/", "history": BASE+"works/hi/", "religion": BASE+"works/re/",
        "letters": BASE+"works/letters/", "difference": BASE+"works/fs/", "faith": BASE+"works/fk/",
    }
    for level in range(1 if args.from_manifest else args.depth + 1):
        batch = [t for t in queue if t[3] not in seen]
        seen.update(t[3] for t in batch)
        if not batch: break
        future_tasks = {}
        next_queue = []
        with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for t in batch:
                # Deliberately re-fetch seeds, so link discovery remains reproducible.
                future_tasks[pool.submit(fetch, t, args.proxy)] = t
            for fut in cf.as_completed(future_tasks):
                t = future_tasks[fut]
                row, links = fut.result()
                known[t[3]] = row
                print(json.dumps({"id": row["id"], "status": row["status"], "bytes": row.get("bytes"), "error": row.get("error")}), flush=True)
                group = t[0].split("__")[0]
                prefix = group_prefix.get(group)
                if t[4] and prefix:
                    for link in links:
                        if link.startswith(prefix) and re.search(r"\.(htm|html)$", link) and link not in seen:
                            slug = urlparse(link).path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
                            next_queue.append((group+"__"+slug, t[1], t[2], link, True))
        MANIFEST.write_text(json.dumps(list(known.values()), ensure_ascii=False, indent=2), encoding="utf-8")
        queue = list({t[3]: t for t in next_queue}.values())
    rows = list(known.values())
    print(json.dumps({"total":len(rows),"ok":sum(x["status"]=="ok" for x in rows),"bytes":sum(x.get("bytes",0) for x in rows)}, indent=2))

if __name__ == "__main__": main()
