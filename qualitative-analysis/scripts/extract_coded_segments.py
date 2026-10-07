#!/usr/bin/env python3
"""Extract code-anchored segments from transcripts coded with Word comments.

Many researchers code in Word rather than in a QDA package: the code label sits
in a comment, and the comment is anchored to the passage it applies to. That
anchor is the verbatim quotation, so it is worth recovering exactly.

Usage:
    python extract_coded_segments.py --corpus transcripts \
        --doc P03:ACT03:ACT03_QC_Qi.docx \
        --doc P11:ACT11:ACT11_QC_Ellaisha.docx \
        --out segments.tsv [--readable segments.txt] [--json]

Writes one row per anchored comment:
    segment_id, participant, study_id, document, anchor_index, comment_id,
    label, span, first_para, crosses_paragraph, exact_in_document

`span` is stored with the register escaping (newlines as \\n, tabs as \\t), which
is the format the quote register expects. Do not escape it a second time.

Read-only with respect to the corpus.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpus_check  # noqa: E402

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
COLUMNS = [
    "segment_id",
    "participant",
    "study_id",
    "document",
    "anchor_index",
    "comment_id",
    "label",
    "span",
    "first_para",
    "crosses_paragraph",
    "exact_in_document",
]


def paragraph_text(paragraph: ET.Element) -> str:
    """Paragraph text exactly as corpus_check's reader sees it."""
    buffer: list[str] = []
    for node in paragraph.iter():
        if node.tag == W + "t":
            buffer.append(node.text or "")
        elif node.tag == W + "tab":
            buffer.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            buffer.append("\n")
    return "".join(buffer)


def comment_labels(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/comments.xml"))
    return {
        comment.get(W + "id"): "".join(
            node.text or "" for node in comment.iter(W + "t")
        ).strip()
        for comment in root.iter(W + "comment")
    }


def anchor_order(path: Path) -> list[str]:
    """Comment ids in the order their ranges open in the document."""
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    order: list[str] = []
    for element in root.iter(W + "commentRangeStart"):
        comment_id = element.get(W + "id")
        if comment_id is not None and comment_id not in order:
            order.append(comment_id)
    return order


def extract_spans(path: Path) -> dict[str, dict[str, object]]:
    """Return {comment_id: span details}.

    A range must be closed on commentRangeEnd. Forgetting to close one makes
    every span run to the end of the document, which is the single easiest way
    to wreck this extraction: the spans then look plausible and match nothing.
    """
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    paragraphs = list(root.iter(W + "p"))
    active: dict[str, list[tuple[int, str]]] = {}
    finished: dict[str, list[tuple[int, str]]] = {}
    unclosed: set[str] = set()

    def append(store: dict[str, list[tuple[int, str]]], comment_id: str,
               index: int, text: str) -> None:
        pieces = store.setdefault(comment_id, [])
        if pieces and pieces[-1][0] == index:
            pieces[-1] = (index, pieces[-1][1] + text)
        else:
            pieces.append((index, text))

    for index, paragraph in enumerate(paragraphs):
        for node in paragraph.iter():
            if node.tag == W + "commentRangeStart":
                comment_id = node.get(W + "id")
                if comment_id is not None:
                    active.setdefault(comment_id, [])
            elif node.tag == W + "commentRangeEnd":
                comment_id = node.get(W + "id")
                if comment_id is not None and comment_id in active:
                    finished[comment_id] = active.pop(comment_id)
            elif node.tag == W + "t":
                for comment_id in active:
                    append(active, comment_id, index, node.text or "")
            elif node.tag == W + "tab":
                for comment_id in active:
                    append(active, comment_id, index, "\t")
            elif node.tag in (W + "br", W + "cr"):
                for comment_id in active:
                    append(active, comment_id, index, "\n")

    for comment_id, pieces in active.items():
        unclosed.add(comment_id)
        finished.setdefault(comment_id, pieces)

    result: dict[str, dict[str, object]] = {}
    for comment_id, pieces in finished.items():
        pieces.sort(key=lambda item: item[0])
        touched = [index for index, _ in pieces]
        result[comment_id] = {
            "text": "\n".join(chunk for _, chunk in pieces),
            "first_para": min(touched) if touched else -1,
            "last_para": max(touched) if touched else -1,
            "crosses_paragraph": len(set(touched)) > 1,
            "unclosed": comment_id in unclosed,
        }
    return result


def parse_document_option(value: str) -> tuple[str, str, str]:
    parts = value.split(":")
    if len(parts) == 3:
        participant, study_id, filename = parts
    elif len(parts) == 2:
        participant, filename = parts
        study_id = Path(filename).stem.split()[0]
    else:
        raise argparse.ArgumentTypeError(
            "use PARTICIPANT:STUDYID:FILENAME.docx (STUDYID is optional)"
        )
    return participant, study_id, filename


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--corpus", required=True, help="directory holding the coded documents")
    parser.add_argument(
        "--doc",
        action="append",
        required=True,
        type=parse_document_option,
        help="PARTICIPANT:STUDYID:FILENAME.docx, repeatable, in the order to number segments",
    )
    parser.add_argument("--out", help="write the segment TSV here")
    parser.add_argument("--readable", help="also write a compact listing for reading")
    parser.add_argument("--json", action="store_true", help="print a JSON summary")
    args = parser.parse_args(argv)

    corpus = Path(args.corpus).expanduser()
    if not corpus.is_dir():
        print(f"corpus directory not found: {corpus}", file=sys.stderr)
        return 2

    rows: list[dict[str, object]] = []
    summary: dict[str, object] = {"documents": {}, "totals": {}}
    problems: list[str] = []

    for participant, study_id, filename in args.doc:
        path = corpus / filename
        if not path.is_file():
            print(f"document not found: {path}", file=sys.stderr)
            return 2
        full_text, _, _ = corpus_check.read_document(path)
        if full_text is None:
            print(f"document could not be read as text: {path}", file=sys.stderr)
            return 2
        labels = comment_labels(path)
        spans = extract_spans(path)
        order = [comment_id for comment_id in anchor_order(path) if comment_id in spans]

        for position, comment_id in enumerate(order, start=1):
            span = spans[comment_id]
            text = str(span["text"])
            if span["unclosed"]:
                problems.append(f"{filename}: comment {comment_id} has no closing anchor")
            if not text.strip():
                problems.append(f"{filename}: comment {comment_id} has an empty anchor")
            rows.append(
                {
                    "segment_id": f"{study_id}-{position:04d}",
                    "participant": participant,
                    "study_id": study_id,
                    "document": filename,
                    "anchor_index": position,
                    "comment_id": comment_id,
                    "label": labels.get(comment_id, ""),
                    "span": text,
                    "first_para": span["first_para"],
                    "crosses_paragraph": span["crosses_paragraph"],
                    "exact_in_document": text in full_text,
                }
            )

        label_counts = Counter(labels.get(comment_id, "") for comment_id in order)
        summary["documents"][filename] = {
            "participant": participant,
            "comments_in_file": len(labels),
            "anchored_comments": len(order),
            "unclosable_or_missing": sorted(set(labels) - set(order)),
            "empty_anchors": sum(1 for cid in order if not str(spans[cid]["text"]).strip()),
            "crosses_paragraph": sum(1 for cid in order if spans[cid]["crosses_paragraph"]),
            "exact_in_document": sum(1 for cid in order if str(spans[cid]["text"]) in full_text),
            "distinct_labels": len(label_counts),
            "duplicate_labels": sorted(
                label for label, count in label_counts.items() if count > 1
            ),
        }

    summary["totals"] = {
        "segments": len(rows),
        "by_participant": dict(Counter(str(row["participant"]) for row in rows)),
        "crosses_paragraph": sum(1 for row in rows if row["crosses_paragraph"]),
        "exact_in_document": sum(1 for row in rows if row["exact_in_document"]),
        "not_exact_in_document": [
            row["segment_id"] for row in rows if not row["exact_in_document"]
        ],
    }

    # Two ways the same words get counted twice: an anchor repeated exactly, and
    # an anchor sitting inside a longer one. Both are invisible in the totals, so
    # they are reported here.
    by_document: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_document.setdefault(str(row["document"]), []).append(row)
    identical: list[tuple[dict[str, object], dict[str, object]]] = []
    nested: list[tuple[dict[str, object], dict[str, object]]] = []
    for document, items in by_document.items():
        for index, first in enumerate(items):
            for second in items[index + 1:]:
                first_span, second_span = str(first["span"]), str(second["span"])
                if first_span == second_span:
                    identical.append((first, second))
                    continue
                shorter, longer = (
                    (first, second) if len(first_span) < len(second_span) else (second, first)
                )
                if str(shorter["span"]) in str(longer["span"]):
                    nested.append((shorter, longer))

    summary["totals"]["identical_anchor_pairs"] = len(identical)
    summary["totals"]["nested_anchor_pairs"] = len(nested)
    summary["overlaps"] = {
        "identical": [
            {
                "document": str(a["document"]),
                "segment_ids": [str(a["segment_id"]), str(b["segment_id"])],
                "labels": [str(a["label"]), str(b["label"])],
            }
            for a, b in identical
        ],
        "nested": [
            {
                "document": str(a["document"]),
                "inner": {"segment_id": str(a["segment_id"]), "label": str(a["label"])},
                "outer": {"segment_id": str(b["segment_id"]), "label": str(b["label"])},
                "inner_chars": len(str(a["span"])),
                "outer_chars": len(str(b["span"])),
            }
            for a, b in nested
        ],
    }

    if args.out:
        target = Path(args.out).expanduser()
        with target.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write("\t".join(COLUMNS) + "\n")
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar=None)
            for row in rows:
                writer.writerow([corpus_check.tsv_escape(str(row[name])) for name in COLUMNS])
        print(f"{len(rows)} segments written to {target}")

    if args.readable:
        target = Path(args.readable).expanduser()
        with target.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(f"{row['segment_id']} | {row['label']}\n    {str(row['span'])[:220]}\n")
        print(f"readable listing written to {target}")

    totals = summary["totals"]
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"documents: {len(summary['documents'])} | segments: {totals['segments']}")
        for name, info in summary["documents"].items():
            print(
                f"  {name}: {info['anchored_comments']} anchored, "
                f"{info['exact_in_document']} exact, {info['crosses_paragraph']} cross-paragraph, "
                f"{len(info['duplicate_labels'])} duplicate label(s)"
            )
        if totals["not_exact_in_document"]:
            print("  anchors not found verbatim in the document text:",
                  ", ".join(totals["not_exact_in_document"]))

    if problems:
        print("\nProblems found:")
        for line in problems:
            print("  -", line)
        return 1
    if totals["not_exact_in_document"]:
        print("\nSome anchors are not byte-identical to the document text. Check them before use.")
        return 1
    if identical or nested:
        print(f"\nAnchors that repeat the same words ({len(identical)} identical pairs, "
              f"{len(nested)} nested pairs). Decide each one before counting:")
        for a, b in identical[:10]:
            print(f"  identical: {a['segment_id']} and {b['segment_id']} "
                  f"({a['label'][:40]!r} / {b['label'][:40]!r})")
        for inner, outer in nested[:20]:
            print(f"  nested:    {inner['segment_id']} inside {outer['segment_id']} "
                  f"({len(str(inner['span']))} of {len(str(outer['span']))} characters)")
        print(
            "  Same code on overlapping text is one coding, not two; different codes on\n"
            "  overlapping text are two readings of one passage - keep both and flag them."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
