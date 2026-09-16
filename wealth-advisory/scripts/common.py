#!/usr/bin/env python3
"""Shared plumbing for the wealth-advisory scripts.

Small on purpose: helpers that every calculator needs, so the conventions for
loading a config, printing a report and writing JSON stay identical across the
suite. Calculator logic does not live here.

Conventions every script in this skill follows:

  * a JSON config in, a markdown report out, optional --json for raw results
  * a missing required field exits 2 with the fields named, never a default
  * money is printed to the precision the input supports
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path


def die(message: str, code: int = 2) -> None:
    sys.stderr.write(str(message).rstrip() + "\n")
    sys.exit(code)


def load_json(path, required: bool = True):
    path = Path(path)
    if not path.exists():
        if required:
            die("File not found: {}".format(path))
        return None
    with open(path, "r", encoding="utf-8-sig") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError as exc:
            die("{} is not valid JSON: {}".format(path, exc))


def require(cfg: dict, keys, where: str = "config") -> None:
    """Exit naming every missing required key, not just the first."""
    missing = [key for key in keys if key not in cfg or cfg[key] is None]
    if missing:
        die(
            "{} is missing required field(s): {}. Nothing is assumed for these - "
            "add them and run again.".format(where, ", ".join(missing))
        )


def money(value: float) -> str:
    return "SGD {:,.0f}".format(value)


def money2(value: float) -> str:
    return "SGD {:,.2f}".format(value)


def pct(value: float) -> str:
    return "{:.2f}%".format(value * 100.0)


def today() -> str:
    return date.today().isoformat()


def stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def emit(report: str, out_path=None, raw=None, json_path=None) -> None:
    """Write the markdown report and, optionally, the machine-readable result."""
    if json_path:
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(raw, handle, indent=2, default=str)
            handle.write("\n")
    if out_path:
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(report)
        sys.stdout.write("Report written to {}\n".format(out_path))
    else:
        sys.stdout.write(report)


def section(title: str, level: int = 2) -> str:
    return "\n{} {}\n".format("#" * level, title)


def table(headers, rows) -> str:
    lines = [
        "| " + " | ".join(str(h) for h in headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)
