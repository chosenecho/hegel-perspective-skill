#!/usr/bin/env python3
"""Reproduce a 20-paragraph, purposefully stratified German Hegel voice sample.

Uses only the standard library and local archived texts. Does not contact the
network or treat these small, deliberately chosen samples as a corpus census.
Run: python scripts/analyze_voice.py [--output PATH]
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = [
    ("PHG01", "phg-de", "pg", "Das Wahre ist das Ganze", "序言¶20", "概念展开"),
    ("PHG02", "phg-de", "pg", "Das Bekannte überhaupt", "序言¶31", "熟知/认识区分"),
    ("PHG03", "phg-de", "pg", "Das Bewußtsein gibt seinen Maßstab an ihm selbst", "导论¶84", "尺度中介"),
    ("PHG04", "phg-de", "pg", "Um das Gesagte durch Beispiele", "序言¶62", "思辨命题例证"),
    ("LOG101", "logic1-de", "pg", "Seyn, reines Seyn", "存在论第一章A", "限定起点"),
    ("LOG102", "logic1-de", "pg", "Aufheben hat in der Sprache", "存在论第一章C.3附注", "双义辨析"),
    ("LOG103", "logic1-de", "pg", "Der Unterschied überhaupt enthält seine beiden Seiten", "本质论第一篇第二章C.1", "对立的内在关系"),
    ("LOG201", "logic2-de", "pg", "Das Allgemeine ist daher die freie Macht", "概念论第一篇第一章A", "普遍/特殊"),
    ("LOG202", "logic2-de", "pg", "Der Zweck ist in seiner Beziehung auf das Mittel", "概念论第二篇第三章C.1", "目的中介"),
    ("LOG203", "logic2-de", "pg", "Was hiermit als Methode hier zu betrachten ist", "概念论第三篇第三章绝对理念", "内容/方法关系"),
    ("SCHOOL01", "school1809-de", "pg", "Ein innerlicher Grund des Zutrauens", "1809-09-29校庆演讲，制度继承段", "实际制度论证"),
    ("SCHOOL02", "school1809-de", "pg", "Das Fortschreiten der Bildung ist nämlich", "同演讲，教养与陌生化段", "教养机制"),
    ("SCHOOL03", "school1809-de", "pg", "Mit diesem mechanischen Momente", "同演讲，语法学习段", "具体课程例子"),
    ("PR01", "zeno-pr__001", "html", "Die unmittelbare Veranlassung zur Herausgabe dieses Grundrisses", "法哲学序言首段", "说明写作目的"),
    ("PR02", "zeno-pr__001", "html", "Das was ist zu begreifen", "法哲学序言，时代的思想段", "定位哲学"),
    ("PR03", "zeno-pr__001", "html", "Um noch über das Belehren", "法哲学序言，猫头鹰段", "意象与限定"),
    ("ABSTRACT01", "zeno-abstract__000", "html", "Denken? Abstrakt?", "谁在抽象地思维首段", "反讽开场"),
    ("ABSTRACT02", "zeno-abstract__000", "html", "Ich brauche für meinen Satz nur Beispiele", "同文，赴刑场杀人犯段", "叙事例证"),
    ("ABSTRACT03", "zeno-abstract__000", "html", "Dies heißt abstrakt gedacht, in dem Mörder", "同文，抽象罪名与感伤段", "反例与限定"),
    ("ABSTRACT04", "zeno-abstract__000", "html", "Alte, ihre Eier sind faul", "同文，鸡蛋争执段", "多声对话/讽刺"),
]

CONTRAST = ("aber", "jedoch", "sondern", "vielmehr", "hingegen", "dagegen", "dennoch", "indes", "einerseits", "andererseits")
FIRST_PERSON = ("ich", "wir", "mir", "mich", "uns")
WORD = re.compile(r"[^\W\d_]+(?:[-’'][^\W\d_]+)*", re.UNICODE)


def clean(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)
    return re.sub(r"\s+", " ", text.replace("_", "")).strip()


class ParagraphReader(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current: list[str] | None = None
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "p":
            if self.current is not None:
                self.paragraphs.append(clean(" ".join(self.current)))
            self.current = []

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "p" and self.current is not None:
            self.paragraphs.append(clean(" ".join(self.current)))
            self.current = None


def paragraphs(source: str, kind: str) -> tuple[Path, list[str], str]:
    if kind == "pg":
        path = ROOT / "references" / "sources" / "books" / f"{source}.txt"
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        # In these archived PG files, wrapped physical lines are separated by
        # two LFs, while paragraph boundaries have at least four. This explicit
        # format assumption is recorded so a changed source fails visibly.
        result = [clean(x) for x in re.split(r"\n{3,}", text)]
    else:
        path = ROOT / "references" / "sources" / "raw" / f"{source}.html"
        raw = path.read_bytes()
        parser = ParagraphReader()
        declared = re.search(br"charset\s*=\s*['\"]?([A-Za-z0-9_-]+)", raw[:8000], re.I)
        encoding = declared.group(1).decode("ascii") if declared else "utf-8-sig"
        parser.feed(raw.decode(encoding))
        parser.close()
        result = parser.paragraphs
    return path, result, hashlib.sha256(raw).hexdigest()


def word_count(text: str) -> int:
    return len(WORD.findall(text))


def sentence_parts(text: str) -> list[str]:
    # A transparent approximation, not a German syntactic parser. Mask a short
    # list of historical abbreviations before splitting terminal punctuation.
    abbr = re.compile(r"\b(?:d\.\s*h\.|d\.\s*i\.|z\.\s*B\.|z\.\s*E\.|u\.\s*s\.\s*f\.|u\.\s*dgl\.|s\.\s*f\.)", re.I)
    masked = abbr.sub(lambda m: m.group().replace(".", "∯"), text)
    items = re.split(r"(?<=[.!?])[\"'»”’\)\]]*\s+", masked)
    return [x.replace("∯", ".") for x in items if WORD.search(x)]


def count_terms(text: str, terms: tuple[str, ...]) -> dict[str, int]:
    return {term: len(re.findall(r"\b" + re.escape(term) + r"\b", text, re.I)) for term in terms}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=ROOT / "references" / "research" / "voice-samples.json")
    args = ap.parse_args()
    cache: dict[tuple[str, str], tuple[Path, list[str], str]] = {}
    samples: list[dict] = []
    all_sentence_lengths: list[int] = []
    for sample_id, source, kind, anchor, locator, function in SPEC:
        if (source, kind) not in cache:
            cache[source, kind] = paragraphs(source, kind)
        path, parts, digest = cache[source, kind]
        matches = [(index, part) for index, part in enumerate(parts) if anchor in part]
        if len(matches) != 1:
            raise SystemExit(f"{sample_id}: expected one paragraph for {anchor!r}, found {len(matches)}")
        index, sample = matches[0]
        lengths = [word_count(s) for s in sentence_parts(sample)]
        if not lengths or word_count(sample) < 10:
            raise SystemExit(f"{sample_id}: empty or unexpectedly short sample")
        all_sentence_lengths.extend(lengths)
        samples.append({
            "id": sample_id, "source_id": source,
            "source_file": path.relative_to(ROOT).as_posix(), "source_sha256": digest,
            "paragraph_index_0_based": index, "anchor": anchor,
            "locator": locator, "function_annotation": function, "text_de": sample,
            "words": word_count(sample), "characters": len(sample),
            "approx_sentences": len(lengths),
            "mean_words_per_sentence": round(statistics.mean(lengths), 2),
            "median_words_per_sentence": statistics.median(lengths),
            "sentence_word_counts": lengths,
            "question_marks": sample.count("?"), "exclamation_marks": sample.count("!"),
            "semicolons": sample.count(";"),
            "contrast_markers": count_terms(sample, CONTRAST),
            "first_person_tokens": count_terms(sample, FIRST_PERSON),
        })
    assert len(samples) == 20
    sources = sorted({s["source_id"] for s in samples})
    aggregate = {
        "sample_count": len(samples), "source_count": len(sources),
        "total_words": sum(s["words"] for s in samples),
        "approx_sentences": sum(s["approx_sentences"] for s in samples),
        "mean_words_per_sentence": round(statistics.mean(all_sentence_lengths), 2),
        "median_words_per_sentence": statistics.median(all_sentence_lengths),
        "min_words_per_sentence": min(all_sentence_lengths),
        "max_words_per_sentence": max(all_sentence_lengths),
        "question_marks": sum(s["question_marks"] for s in samples),
        "exclamation_marks": sum(s["exclamation_marks"] for s in samples),
        "semicolons": sum(s["semicolons"] for s in samples),
        "contrast_markers": {k: sum(s["contrast_markers"][k] for s in samples) for k in CONTRAST},
        "first_person_tokens": {k: sum(s["first_person_tokens"][k] for s in samples) for k in FIRST_PERSON},
    }
    by_source = []
    for source in sources:
        group = [s for s in samples if s["source_id"] == source]
        sl = [n for s in group for n in s["sentence_word_counts"]]
        by_source.append({
            "source_id": source, "sample_count": len(group),
            "words": sum(s["words"] for s in group), "approx_sentences": len(sl),
            "mean_words_per_sentence": round(statistics.mean(sl), 2),
            "median_words_per_sentence": statistics.median(sl),
            "question_marks": sum(s["question_marks"] for s in group),
        })
    report = {
        "study_date": "2026-11-03", "language": "de",
        "sampling": "Purposeful stratification: 20 author-text paragraphs across 6 archived sources; unique anchors, no random/representative claim.",
        "limitations": [
            "Digital transcription, historical spelling and editorial paragraph boundaries affect counts.",
            "Approximate punctuation-based sentence splitting; no inference about all Hegel texts or spoken delivery.",
            "Deliberately includes exposition, public speech, irony and examples; genre mix is not population-weighted.",
            "Pronouns in quoted comic dialogue are not necessarily the author's own voice; markers do not prove semantics.",
            "No automatic counts of metaphors, truth, uncertainty or philosophical quality are claimed.",
        ],
        "aggregate": aggregate, "by_source": by_source, "samples": samples,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "aggregate": aggregate, "by_source": by_source}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
