# -*- coding: utf-8 -*-
"""
Verification gates for a qualitative coding deliverable.

    python check_coding.py --source codes.xlsx --deliverable coded.xlsx
    python check_coding.py --source codes.xlsx --deliverable v2.xlsx --previous v1.xlsx

Checks the artifact, not the interpretation. A clean run means the workbook is
internally consistent and faithful to the source; it does not mean the coding is
right. Say which is which when reporting.

Columns are found by header substring, so the sheet layout is free as long as
the headers say what they are.
"""
import argparse
import os
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xlsx_io import load_sheet, sheet_names  # noqa: E402

MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
DIRECTIONAL = ["affect", "influence", "impact", "determine", "cause",
               "relate", "predict"]


class Report:
    def __init__(self):
        self.fails = []
        self.checks = 0

    def check(self, cond, msg):
        self.checks += 1
        print(("  ok  " if cond else "  **  ") + msg)
        if not cond:
            self.fails.append(msg)
        return bool(cond)

    def done(self):
        print()
        if self.fails:
            print("FAILED %d of %d check(s):" % (len(self.fails), self.checks))
            for f in self.fails:
                print("  -", f)
            return 1
        print("ALL %d CHECKS PASSED" % self.checks)
        print("Scope: internal consistency and source fidelity only, "
              "not the correctness of the coding.")
        return 0


def col(header, *needles, required=True, exclude=None):
    """First header containing every needle. `exclude` skips headers containing it.

    Always pass exclude='grand' when searching for 'parent': the substring
    'parent' occurs inside 'grandparent', so a plain search finds the wrong
    column on any sheet that carries both.
    """
    for i, h in enumerate(header):
        hl = str(h).lower()
        if exclude and exclude.lower() in hl:
            continue
        if all(n.lower() in hl for n in needles):
            return i
    if required:
        raise SystemExit("no column matching %s in header: %s" % (needles, header))
    return None


def pad(rows):
    """Equalise row widths; a row whose trailing cells are empty comes back short."""
    if not rows:
        return rows
    w = max(len(r) for r in rows)
    return [list(r) + [""] * (w - len(r)) for r in rows]


def sheet(path, which):
    return pad(load_sheet(path, which))


def find_sheet(path, *needles):
    """1-based index of the first sheet whose header carries every needle.

    Sheet positions move between passes, so never hard-code the log's index:
    a previous deliverable with three sheets keeps its log somewhere other than
    the current one with five.
    """
    for i in range(1, len(sheet_names(path)) + 1):
        rows = sheet(path, i)
        if not rows:
            continue
        hdr = [str(h).lower() for h in rows[0]]
        if all(any(n in h for h in hdr) for n in needles):
            return i
    return None


def prefix(code):
    return str(code).split(" ")[0]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, help="original code list workbook")
    p.add_argument("--deliverable", required=True)
    p.add_argument("--source-sheet", default="1")
    p.add_argument("--coded-sheet", default="1")
    p.add_argument("--log-sheet", default="auto",
                   help="index, sheet name, or 'auto' to find by header")
    p.add_argument("--framework-sheet", default="3", help="'' to skip")
    p.add_argument("--revision-sheet", default="5", help="'' to skip")
    p.add_argument("--previous", help="prior deliverable, for the revision-log cross-check")
    p.add_argument("--question", help="the stated analytic question, if any")
    args = p.parse_args()

    def as_sheet(v):
        return int(v) if str(v).isdigit() else v

    r = Report()

    # ---------------------------------------------------------------- source
    src_rows = sheet(args.source, as_sheet(args.source_sheet))
    sh = src_rows[0]
    s_id = col(sh, "code id")
    s_quote = col(sh, "highlighted")
    s_code = col(sh, "comment", required=False)
    src = {str(row[s_id]): row for row in src_rows[1:] if str(row[s_id]).strip() != ""}
    print("source: %d data rows, %d unique ids" % (len(src_rows) - 1, len(src)))
    r.check(len(src) == len(src_rows) - 1, "source ids are unique")

    # ------------------------------------------------------------- deliverable
    print("\ndeliverable sheets: %s" % ", ".join(sheet_names(args.deliverable)))
    coded_rows = sheet(args.deliverable, as_sheet(args.coded_sheet))
    ch = coded_rows[0]
    c_id = col(ch, "code id")
    c_gp = col(ch, "grandparent")
    c_p = col(ch, "parent", exclude="grand")
    c_quote = col(ch, "highlighted", required=False)
    c_code = col(ch, "comment", required=False)
    coded = [row for row in coded_rows[1:] if str(row[c_id]).strip() != ""]

    print("\n-- coded sheet")
    ids = [str(row[c_id]) for row in coded]
    r.check(len(ids) == len(set(ids)), "no duplicate code ids (%d coded)" % len(ids))
    r.check(all(i in src for i in ids),
            "every coded id exists in the source (orphans: %s)"
            % [i for i in ids if i not in src])
    r.check(all(str(row[c_gp]).strip() and str(row[c_p]).strip() for row in coded),
            "every coded row has a parent and a grandparent")

    bad_nest = [str(row[c_id]) for row in coded
                if prefix(row[c_p]).split(".")[0] != prefix(row[c_gp])]
    r.check(not bad_nest,
            "every parent nests under its grandparent (bad: %s)" % bad_nest[:10])

    if c_quote is not None:
        mis = [i for i, row in zip(ids, coded) if src[i][s_quote] != row[c_quote]]
        r.check(not mis, "quotations byte-identical to source (mismatch: %s)" % mis[:10])
    if c_code is not None and s_code is not None:
        mis = [i for i, row in zip(ids, coded) if src[i][s_code] != row[c_code]]
        r.check(not mis, "leaf codes byte-identical to source (mismatch: %s)" % mis[:10])

    # ------------------------------------------------------------------- log
    log_sheet = args.log_sheet
    if str(log_sheet).lower() == "auto":
        log_sheet = find_sheet(args.deliverable, "decision", "reason")
        if log_sheet is None:
            raise SystemExit("no screening log sheet found in the deliverable "
                             "(a sheet whose header carries Decision and Reason)")
    log_rows = sheet(args.deliverable, as_sheet(log_sheet))
    lh = log_rows[0]
    l_id = col(lh, "code id")
    l_dec = col(lh, "decision")
    l_why = col(lh, "reason")
    log = [row for row in log_rows[1:] if str(row[l_id]).strip() != ""]

    print("\n-- screening log")
    log_ids = [str(row[l_id]) for row in log]
    r.check(len(log_ids) == len(set(log_ids)), "each source item screened exactly once")
    r.check(set(log_ids) == set(src),
            "screening log covers every source item (missing: %s, extra: %s)"
            % (sorted(set(src) - set(log_ids))[:10],
               sorted(set(log_ids) - set(src))[:10]))
    r.check(all(str(row[l_why]).strip() for row in log),
            "every screened item carries a reason")
    r.check(all(str(row[l_dec]).strip() in ("Include", "Borderline", "Exclude")
                for row in log),
            "decision vocabulary is closed (Include / Borderline / Exclude)")
    included = {str(row[l_id]) for row in log if str(row[l_dec]).strip() == "Include"}
    r.check(included == set(ids), "log Include set == coded set, both directions")
    counts = {}
    for row in log:
        d = str(row[l_dec]).strip()
        counts[d] = counts.get(d, 0) + 1
    print("   decisions: %s (total %d)" % (counts, len(log)))

    # ------------------------------------------------------------- framework
    if str(args.framework_sheet) not in ("", "None"):
        fw_rows = sheet(args.deliverable, as_sheet(args.framework_sheet))
        fh = fw_rows[0]
        f_ids = col(fh, "code ids", required=False)
        if f_ids is None:
            f_ids = col(fh, "code id", exclude="grand")
        f_n = col(fh, "no. of", required=False)
        members, total = [], 0
        for row in fw_rows[1:]:
            if not str(row[0]).strip():
                continue
            members += [x.strip() for x in str(row[f_ids]).split(",") if x.strip()]
            if f_n is not None and str(row[f_n]).strip().isdigit():
                total += int(row[f_n])
        print("\n-- framework")
        r.check(sorted(members) == sorted(ids),
                "framework membership == coded set (diff: %s)"
                % sorted(set(members) ^ set(ids))[:10])
        if f_n is not None:
            r.check(total == len(ids),
                    "per-parent counts sum to %d (got %d)" % (len(ids), total))

    # -------------------------------------------------------------- question
    if args.question:
        print("\n-- analytic question")
        q = args.question.lower()
        r.check(q.startswith(("how", "what")), "question begins with how/what")
        hits = [w for w in DIRECTIONAL if w in q]
        r.check(not hits, "question free of directional verbs (found: %s)" % hits)

    # ----------------------------------------------------------- revision log
    if args.previous and str(args.revision_sheet) not in ("", "None"):
        print("\n-- revision log vs previous artifact")
        prev_log_sheet = find_sheet(args.previous, "decision", "reason")
        if prev_log_sheet is None:
            raise SystemExit("no screening log found in the previous workbook")
        prev_log = sheet(args.previous, prev_log_sheet)
        plh = prev_log[0]
        p_id = col(plh, "code id")
        p_dec = col(plh, "decision")
        prev_dec = {str(row[p_id]): str(row[p_dec]).strip()
                    for row in prev_log[1:] if str(row[p_id]).strip() != ""}
        prev_inc = {i for i, d in prev_dec.items() if d == "Include"}
        now_dec = {str(row[l_id]): str(row[l_dec]).strip() for row in log}

        rev_rows = sheet(args.deliverable, as_sheet(args.revision_sheet))
        rh = rev_rows[0]
        r_id = col(rh, "code id")
        r_before = col(rh, "v1 decision", required=False)
        if r_before is None:
            r_before = col(rh, "before", required=False, exclude="after")
        r_after = col(rh, "v2 decision", required=False)
        if r_after is None:
            r_after = col(rh, "after", required=False)
        rev = [row for row in rev_rows[1:] if str(row[r_id]).strip() != ""]

        mismatch = []
        for row in rev:
            i = str(row[r_id])
            if r_before is not None and prev_dec.get(i) != str(row[r_before]).strip():
                mismatch.append("%s: logged before=%r, file says %r"
                                % (i, row[r_before], prev_dec.get(i)))
            if r_after is not None and now_dec.get(i) != str(row[r_after]).strip():
                mismatch.append("%s: logged after=%r, file says %r"
                                % (i, row[r_after], now_dec.get(i)))
        r.check(not mismatch,
                "logged before/after values match both files (%s)" % mismatch[:6])

        logged = {str(row[r_id]) for row in rev}
        undocumented = sorted(i for i in prev_dec
                              if prev_dec[i] != now_dec.get(i) and i not in logged)
        r.check(not undocumented,
                "no undocumented decision changes (%s)" % undocumented[:10])
        gone = sorted(prev_inc - included)
        unlogged = [g for g in gone if g not in logged]
        r.check(not unlogged,
                "every item that left the coded set is logged (unlogged: %s)" % unlogged)
        print("   %d items left the coded set; %d revision entries" % (len(gone), len(rev)))

    # --------------------------------------------------------------- plumbing
    print("\n-- workbook integrity")
    with zipfile.ZipFile(args.deliverable) as z:
        names = set(z.namelist())
        r.check(z.testzip() is None, "zip integrity")
        broken = []
        for n in sorted(names):
            if n.endswith((".xml", ".rels")):
                try:
                    ET.fromstring(z.read(n))
                except Exception as e:  # noqa: BLE001
                    broken.append("%s: %s" % (n, e))
        r.check(not broken, "every part is well-formed XML (%s)" % broken[:3])
        ct = ET.fromstring(z.read("[Content_Types].xml"))
        declared = {e.get("PartName") for e in ct if e.tag.endswith("Override")}
        defaults = {e.get("Extension") for e in ct if e.tag.endswith("Default")}
        missing = [n for n in names
                   if not n.endswith(".rels")
                   and "/" + n not in declared
                   and n.rsplit(".", 1)[-1] not in defaults]
        r.check(not missing, "every part has a content type (%s)" % missing[:5])
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        unresolved = [rel.get("Target") for rel in rels
                      if ("xl/" + rel.get("Target")).replace("xl//", "xl/") not in names]
        r.check(not unresolved, "every relationship target exists (%s)" % unresolved[:5])

    print("\nRemaining manual gate: confirm the workbook opens in Excel without a "
          "repair prompt (see references/xlsx-mechanics.md).")
    return r.done()


if __name__ == "__main__":
    sys.exit(main())
