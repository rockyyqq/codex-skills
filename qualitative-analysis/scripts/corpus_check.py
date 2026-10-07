#!/usr/bin/env python3
"""Corpus checks for qualitative analysis.

    inventory  what is in the corpus, what can be read, what is duplicated or
               cloud-dehydrated
    extract    pull candidate quotations out of a delivered report into a register
    verify     check a quotation register against the corpus

Standard library only. Reads source material; never writes to it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

READABLE_TEXT_EXT = {".txt", ".md", ".markdown", ".text", ".log", ".vtt", ".srt"}
READABLE_ZIP_EXT = {".docx"}
CONVERT_FIRST_EXT = {".rtf", ".odt", ".pdf", ".htm", ".html", ".epub", ".doc", ".pages"}
SKIP_NAMES = {"thumbs.db", "desktop.ini", ".ds_store"}

NS_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

TRY_ENCODINGS = ("utf-8-sig", "utf-8", "utf-16", "cp1252")

FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
BLOCKQUOTE_RE = re.compile(r"^\s{0,3}>\s?(.*)$")
QUOTED_RE = re.compile(r"\u201c([^\u201d\n]{2,})\u201d|\"([^\"\n]{2,})\"")
MASK_RE = re.compile(r"\[[^\]]*\]")

DEFAULT_MIN_QUOTE_CHARS = 8
MIN_BLOCKQUOTE_CHARS = 3

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2


def configure_stdout() -> None:
    """Keep non-ASCII report text from crashing on a Windows console."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def out(text: str = "") -> None:
    print(text)


def clip(text: str, width: int = 64) -> str:
    flat = text.replace("\n", "\\n").replace("\r", "")
    return flat if len(flat) <= width else flat[: width - 1] + "\u2026"


# ---------------------------------------------------------------- file reading


def read_text_with_encoding(path: Path) -> tuple[str | None, str, str]:
    """Return (text, encoding, note). text is None when unreadable.

    Line endings are translated to \\n on read. CRLF is a file-format artifact of
    the machine that wrote the file, not part of what the participant said, so
    comparing across it would report false mismatches. Nothing else is normalised:
    spacing, punctuation and encoding are carried through as they are.
    """
    for encoding in TRY_ENCODINGS:
        try:
            with open(path, "r", encoding=encoding, newline=None) as handle:
                return handle.read(), encoding, ""
        except UnicodeDecodeError:
            continue
        except PermissionError as exc:
            return (
                None,
                "",
                f"read failed: {exc.strerror or exc} - if this file is on OneDrive or "
                "Dropbox it may be a dehydrated placeholder; copy it to hydrate it, "
                "then read the copy",
            )
        except OSError as exc:
            return None, "", f"read failed: {exc}"
    return None, "", f"could not decode as any of {', '.join(TRY_ENCODINGS)}"


def read_docx_text(path: Path) -> tuple[str | None, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            if "word/document.xml" not in archive.namelist():
                return None, "not a Word document (no word/document.xml)"
            with archive.open("word/document.xml") as handle:
                tree = ET.parse(handle)
    except PermissionError as exc:
        return None, f"read failed: {exc.strerror or exc} - possible dehydrated placeholder"
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        return None, f"read failed: {exc}"

    paragraphs: list[str] = []
    for paragraph in tree.iter(NS_W + "p"):
        buffer: list[str] = []
        for node in paragraph.iter():
            if node.tag == NS_W + "t":
                buffer.append(node.text or "")
            elif node.tag == NS_W + "tab":
                buffer.append("\t")
            elif node.tag in (NS_W + "br", NS_W + "cr"):
                buffer.append("\n")
        paragraphs.append("".join(buffer))
    return "\n".join(paragraphs), ""


def read_document(path: Path) -> tuple[str | None, str, str]:
    """Return (text, source, note) for any supported document."""
    suffix = path.suffix.lower()
    if suffix in READABLE_TEXT_EXT:
        text, encoding, note = read_text_with_encoding(path)
        return text, f"text/{encoding}" if text is not None else "", note
    if suffix in READABLE_ZIP_EXT:
        text, note = read_docx_text(path)
        return text, "docx" if text is not None else "", note
    if suffix in CONVERT_FIRST_EXT:
        return None, "", f"{suffix} is not readable as text; convert it to .txt or .docx first"
    return None, "", f"unsupported format {suffix or '(none)'}"


def file_notes(path: Path) -> list[str]:
    notes: list[str] = []
    try:
        info = os.stat(path)
    except OSError as exc:
        return [f"stat failed: {exc}"]
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    offline = getattr(stat, "FILE_ATTRIBUTE_OFFLINE", 0x1000)
    if attributes & reparse:
        notes.append("cloud-placeholder")
    if attributes & offline:
        notes.append("offline")
    return notes


def list_corpus(corpus: Path) -> list[Path]:
    if not corpus.is_dir():
        raise SystemExit(f"corpus directory not found: {corpus}")
    files = []
    for path in sorted(corpus.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(corpus).parts):
            continue
        if path.name.lower() in SKIP_NAMES or path.name.startswith("~$"):
            continue
        files.append(path)
    return files


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


# ---------------------------------------------------------------- inventory


def cmd_inventory(args: argparse.Namespace) -> int:
    corpus = Path(args.corpus).expanduser()
    files = list_corpus(corpus)

    rows = []
    digests: dict[str, list[str]] = {}
    unreadable: list[str] = []
    unreadable_documents: list[str] = []
    placeholders: list[str] = []
    empty: list[str] = []
    short: list[str] = []

    for path in files:
        rel = path.relative_to(corpus).as_posix()
        notes = file_notes(path)
        text, source, note = read_document(path)
        chars = len(text) if text is not None else 0
        words = len(re.findall(r"\S+", text)) if text is not None else 0
        if "cloud-placeholder" in notes:
            placeholders.append(rel)
        if text is None:
            unreadable.append(rel)
            if note:
                unreadable_documents.append(f"{rel}: {note}")
        else:
            if chars < 50:
                empty.append(rel)
            elif chars < 1500:
                short.append(rel)
            try:
                digests.setdefault(sha256_of(path), []).append(rel)
            except OSError:
                pass
        rows.append(
            {
                "file": rel,
                "format": path.suffix.lower() or "(none)",
                "readable": text is not None,
                "source": source,
                "chars": chars,
                "words": words,
                "notes": "; ".join(notes + ([note] if note else [])),
            }
        )

    duplicates = [
        {"content_hash": digest[:12], "files": names}
        for digest, names in digests.items()
        if len(names) > 1
    ]

    if args.json:
        payload = {
            "corpus": str(corpus),
            "documents": len(files),
            "files": rows,
            "duplicates": duplicates,
            "cloud_placeholders": placeholders,
            "unreadable": unreadable,
            "empty": empty,
            "unexpectedly_short": short,
        }
        out(json.dumps(payload, indent=2, ensure_ascii=False))
        return EXIT_OK

    out(f"Corpus: {corpus}")
    out(f"Documents: {len(files)}")
    out("")
    header = f"{'file':52} {'format':9} {'read':5} {'chars':>8} {'words':>7}  notes"
    out(header)
    out("-" * len(header))
    for row in rows:
        out(
            f"{clip(row['file'], 52):52} {row['format']:9} "
            f"{'yes' if row['readable'] else 'NO':5} {row['chars']:>8} {row['words']:>7}  {row['notes']}"
        )

    out("")
    if not files:
        out("No documents found. Check the corpus path before going further.")
        return EXIT_FAILED
    if placeholders:
        out("Cloud placeholders (the file is not on disk; copy it to hydrate it):")
        for rel in placeholders:
            out(f"  - {rel}")
    if unreadable_documents:
        out("Not readable as text:")
        for line in unreadable_documents:
            out(f"  - {line}")
    if duplicates:
        out("Duplicate content under more than one name (this double-counts evidence):")
        for group in duplicates:
            out(f"  - {', '.join(group['files'])}")
    if empty:
        out("Empty or near-empty (<50 characters) - a failed export, not a short document:")
        for rel in empty:
            out(f"  - {rel}")
    if short:
        out("Unexpectedly short (<1500 characters) - check these are complete:")
        for rel in short:
            out(f"  - {rel}")

    readable = len(files) - len(unreadable)
    out("")
    out(f"Readable: {readable} of {len(files)}.")
    if unreadable:
        out("Everything below can read only the readable documents. Say so in the deliverable.")
    return EXIT_OK


# ---------------------------------------------------------------- extract


def tsv_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\t", "\\t")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
    )


def tsv_unescape(value: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char == "\\" and index + 1 < len(value):
            following = value[index + 1]
            if following == "n":
                result.append("\n")
                index += 2
                continue
            if following == "t":
                result.append("\t")
                index += 2
                continue
            if following == "\\":
                result.append("\\")
                index += 2
                continue
        result.append(char)
        index += 1
    return "".join(result)


def collect_quotations(text: str, min_chars: int) -> list[str]:
    """Candidate quotations: Markdown blockquotes, then double-quoted spans."""
    quotes: list[str] = []
    lines = text.splitlines()
    in_fence = False
    index = 0
    plain_lines: list[str] = []

    while index < len(lines):
        line = lines[index]
        if FENCE_RE.match(line):
            in_fence = not in_fence
            index += 1
            continue
        if in_fence:
            index += 1
            continue
        blockquote = BLOCKQUOTE_RE.match(line)
        if blockquote:
            run = [blockquote.group(1)]
            index += 1
            while index < len(lines):
                following = BLOCKQUOTE_RE.match(lines[index])
                if not following:
                    break
                run.append(following.group(1))
                index += 1
            candidate = "\n".join(run).strip()
            if len(candidate) >= MIN_BLOCKQUOTE_CHARS:
                quotes.append(candidate)
            continue
        plain_lines.append(line)
        index += 1

    for match in QUOTED_RE.finditer("\n".join(plain_lines)):
        candidate = (match.group(1) or match.group(2) or "").strip()
        if len(candidate) >= min_chars:
            quotes.append(candidate)

    deduped: list[str] = []
    seen: set[str] = set()
    for quote in quotes:
        if quote not in seen:
            seen.add(quote)
            deduped.append(quote)
    return deduped


def cmd_extract(args: argparse.Namespace) -> int:
    deliverable = Path(args.deliverable).expanduser()
    text, source, note = read_document(deliverable)
    if text is None:
        out(f"Could not read {deliverable}: {note or 'unsupported format'}")
        return EXIT_USAGE

    quotes = collect_quotations(text, args.min_chars)
    if not quotes:
        out(f"No candidate quotations found in {deliverable}.")
        out("Quotations are recognised as Markdown blockquotes or double-quoted spans.")
        return EXIT_OK

    rows = ["\t".join(["quote_id", "quote", "source_document", "location", "status"])]
    for number, quote in enumerate(quotes, start=1):
        rows.append(
            "\t".join(
                [
                    f"Q{number:03d}",
                    tsv_escape(quote),
                    "",
                    "",
                    "UNVERIFIED",
                ]
            )
        )
    payload = "\n".join(rows) + "\n"

    if args.out:
        target = Path(args.out).expanduser()
        target.write_text(payload, encoding="utf-8")
        out(f"{len(quotes)} candidate quotations written to {target}")
        out("Fill source_document and location for every row, then run: verify "
            f"--register {target} --corpus <corpus dir>")
    else:
        out(payload.rstrip("\n"))
    return EXIT_OK


# ---------------------------------------------------------------- verify


def normalize_ws(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def build_index(corpus: Path) -> tuple[dict[str, Path], list[Path]]:
    files = list_corpus(corpus)
    index: dict[str, Path] = {}
    for path in files:
        rel = path.relative_to(corpus).as_posix()
        for key in (rel, rel.lower(), path.name, path.name.lower(), path.stem, path.stem.lower()):
            index.setdefault(key, path)
    return index, files


def resolve_source(name: str, index: dict[str, Path], files: list[Path]) -> tuple[Path | None, str]:
    """Resolve a register source name. Returns (path, note)."""
    if not name:
        return None, ""
    for key in (
        name,
        name.lower(),
        Path(name).name,
        Path(name).name.lower(),
        Path(name).stem,
        Path(name).stem.lower(),
    ):
        found = index.get(key)
        if found is not None:
            return found, ""

    needle = Path(name).name.lower()
    matches = [
        path
        for path in files
        if path.name.lower().startswith(needle) or path.stem.lower().startswith(needle)
    ]
    if len(matches) == 1:
        return matches[0], f"matched by prefix: {matches[0].name}"
    if len(matches) > 1:
        names = ", ".join(sorted(path.name for path in matches))
        return None, f"ambiguous source name, matches: {names}"
    return None, ""


def read_register(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8-sig")
    rows: list[dict[str, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split("\t")
        if number == 1 and fields[0].strip().lower() == "quote_id":
            continue
        while len(fields) < 5:
            fields.append("")
        rows.append(
            {
                "line": str(number),
                "quote_id": fields[0].strip(),
                "quote": fields[1],
                "source_document": fields[2].strip(),
                "location": fields[3].strip(),
                "status": fields[4].strip(),
            }
        )
    return rows


def result(status: str, detail: str = "", path: Path | None = None, offset: int = -1,
           normalized: bool = False) -> dict[str, object]:
    return {
        "status": status,
        "detail": detail,
        "path": path,
        "offset": offset,
        "normalized": normalized,
    }


def check_row(
    row: dict[str, str],
    index: dict[str, Path],
    files: list[Path],
    all_text: dict[Path, str],
) -> dict[str, object]:
    quote = tsv_unescape(row["quote"])
    declared_masked = row["status"].strip().lower().startswith("masked")

    target, note = resolve_source(row["source_document"], index, files)
    if note.startswith("ambiguous"):
        return result("ambiguous-source", note)
    if row["source_document"] and target is None:
        return result("source-not-found", f"no corpus file matches {row['source_document']!r}")

    candidates = [target] if target is not None else files
    readable = [path for path in candidates if path in all_text]
    if not readable:
        return result("unreadable", "the named document could not be read as text")

    if declared_masked:
        fragments = [part.strip() for part in MASK_RE.split(quote)]
        fragments = [part for part in fragments if part]
        if not fragments:
            return result("fail", "row is marked masked but holds no verifiable fragment")
        for path in readable:
            text = all_text[path]
            cursor = 0
            for fragment in fragments:
                position = text.find(fragment, cursor)
                if position < 0:
                    break
                cursor = position + len(fragment)
            else:
                return result(
                    "masked",
                    f"all {len(fragments)} unmasked fragments found in order",
                    path,
                    cursor,
                )
        for path in readable:
            normalized_text = normalize_ws(all_text[path])
            cursor = 0
            for fragment in fragments:
                position = normalized_text.find(normalize_ws(fragment), cursor)
                if position < 0:
                    break
                cursor = position + len(normalize_ws(fragment))
            else:
                return result(
                    "masked-whitespace",
                    f"{len(fragments)} fragments matched only after whitespace normalisation",
                    path,
                    cursor,
                    normalized=True,
                )
        return result("fail", "unmasked fragments not found in order")

    for path in readable:
        position = all_text[path].find(quote)
        if position >= 0:
            return result("exact", "", path, position)
    for path in readable:
        position = normalize_ws(all_text[path]).find(normalize_ws(quote))
        if position >= 0:
            return result("whitespace", "", path, position, normalized=True)
    return result("fail", "not found in the corpus")


def cmd_verify(args: argparse.Namespace) -> int:
    register = Path(args.register).expanduser()
    corpus = Path(args.corpus).expanduser()
    if not register.is_file():
        out(f"register not found: {register}")
        return EXIT_USAGE

    index, files = build_index(corpus)
    all_text: dict[Path, str] = {}
    unreadable: list[str] = []
    for path in files:
        text, _, note = read_document(path)
        if text is None:
            unreadable.append(f"{path.relative_to(corpus).as_posix()}: {note}")
            continue
        all_text[path] = text
    if not all_text:
        out("No readable documents in the corpus; nothing can be verified.")
        return EXIT_FAILED

    rows = read_register(register)
    if not rows:
        out(f"No rows in {register}.")
        return EXIT_USAGE

    counts: dict[str, int] = {}
    attention: list[str] = []
    cited: set[Path] = set()
    PASSING = ("exact", "masked")

    for row in rows:
        check = check_row(row, index, files, all_text)
        status = str(check["status"])
        counts[status] = counts.get(status, 0) + 1
        path = check["path"]
        offset = int(check["offset"])  # type: ignore[arg-type]
        where = path.name if isinstance(path, Path) else ""
        if isinstance(path, Path) and status in PASSING + ("masked-whitespace", "whitespace"):
            cited.add(path)
        marker = "~" if check["normalized"] and offset >= 0 else "@"
        spot = f"{where} {marker}{offset}" if where and offset >= 0 else where
        quoted = tsv_unescape(row["quote"])
        detail = str(check["detail"])
        out(f"{row['quote_id']:>6}  {status:<17} {spot or detail}  {clip(quoted, 50)}")
        if status not in PASSING:
            attention.append(f"{row['quote_id']} ({status}) {clip(quoted, 58)}")

    out("")
    out(f"Register: {register}  rows: {len(rows)}")
    for status in sorted(counts):
        out(f"  {status}: {counts[status]}")

    uncited = [
        path.relative_to(corpus).as_posix() for path in files if path in all_text and path not in cited
    ]
    if uncited:
        out("")
        out("Corpus documents not cited by any register row (account for each in the deliverable):")
        for rel in uncited[:25]:
            out(f"  - {rel}")
        if len(uncited) > 25:
            out(f"  ... and {len(uncited) - 25} more")

    if unreadable:
        out("")
        out("Documents that could not be read (they cannot be verified):")
        for line in unreadable:
            out(f"  - {line}")

    out("")
    if counts.get("whitespace") or counts.get("masked-whitespace"):
        out(
            "Whitespace-only matches are reported, not passed: those quotations are not "
            "byte-identical to the source. Fix the quotation, or say in the deliverable "
            "that it is a re-wrapped quotation rather than verbatim."
        )
    if counts.get("masked"):
        out("Masked rows verified: report the masked count in the deliverable.")
    if attention:
        out("")
        out(f"{len(attention)} row(s) need attention before delivery:")
        for line in attention:
            out(f"  - {line}")
        out("")
        out("Do not deliver a quotation that failed, and do not edit the source to match it.")
        return EXIT_FAILED

    out("")
    out(
        "All rows verified against the corpus. This proves the quotations are faithful; "
        "it does not prove the coding is right."
    )
    return EXIT_OK


# ---------------------------------------------------------------- cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Corpus checks for qualitative analysis (read-only).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory", help="report what the corpus holds")
    inventory.add_argument("--corpus", required=True, help="corpus directory")
    inventory.add_argument("--json", action="store_true", help="emit JSON")
    inventory.set_defaults(func=cmd_inventory)

    extract = subparsers.add_parser("extract", help="pull candidate quotations from a report")
    extract.add_argument("--deliverable", required=True, help="the delivered report (.md, .txt, .docx)")
    extract.add_argument("--out", help="register TSV to write (default: stdout)")
    extract.add_argument(
        "--min-chars",
        type=int,
        default=DEFAULT_MIN_QUOTE_CHARS,
        help=f"minimum length for a quoted span (default {DEFAULT_MIN_QUOTE_CHARS})",
    )
    extract.set_defaults(func=cmd_extract)

    verify = subparsers.add_parser("verify", help="check a register against the corpus")
    verify.add_argument("--register", required=True, help="register TSV")
    verify.add_argument("--corpus", required=True, help="corpus directory")
    verify.set_defaults(func=cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
