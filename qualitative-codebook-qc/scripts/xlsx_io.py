# -*- coding: utf-8 -*-
"""
Standard-library XLSX reader and writer.

Written for environments with no spreadsheet library and no working pip.
Handles both inline strings (script-written workbooks) and shared strings
(Excel-written workbooks), which is the failure that silently returns blanks.

    from xlsx_io import load_sheet, write_xlsx
    rows = load_sheet("codes.xlsx", sheet=1)
    write_xlsx("out.xlsx", [("Codes", rows, [8, 60, 40])])
"""
import re
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"m": MAIN}


# ----------------------------------------------------------------- reading
def sheet_names(path):
    """Worksheet names, in workbook order."""
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
    return [s.get("name") for s in wb.iter("{%s}sheet" % MAIN)]


def _col_index(ref):
    letters = re.match(r"([A-Z]+)", ref).group(1)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _shared_strings(z):
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.iter("{%s}t" % MAIN))
            for si in root.findall("m:si", NS)]


def load_sheet(path, sheet=1):
    """Rows of one sheet as lists of strings. `sheet` is a 1-based index or a name."""
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n)]
        names.sort(key=lambda n: int(re.search(r"(\d+)", n.split("/")[-1]).group(1)))
        if isinstance(sheet, str):
            idx = sheet_names(path).index(sheet)
        else:
            idx = sheet - 1
        if idx < 0 or idx >= len(names):
            raise IndexError("no sheet %r; workbook has %d" % (sheet, len(names)))
        shared = _shared_strings(z)
        root = ET.fromstring(z.read(names[idx]))

    rows = []
    for row in root.iter("{%s}row" % MAIN):
        cells = {}
        for c in row.findall("m:c", NS):
            ref, t = c.get("r"), c.get("t")
            v = c.find("m:v", NS)
            if t == "inlineStr":
                is_el = c.find("m:is", NS)
                val = "" if is_el is None else "".join(
                    x.text or "" for x in is_el.iter("{%s}t" % MAIN))
            elif t == "s" and v is not None:
                val = shared[int(v.text)]
            elif v is not None:
                val = v.text
            else:
                val = ""
            cells[_col_index(ref)] = val or ""
        width = max(cells) + 1 if cells else 0
        rows.append([cells.get(i, "") for i in range(width)])
    return rows


def load_workbook(path, sheets=None):
    """{sheet name: rows} for the requested sheets (default: all)."""
    want = sheets or sheet_names(path)
    return {n: load_sheet(path, n) for n in want}


# ----------------------------------------------------------------- writing
def col_letter(idx):
    s, idx = "", idx + 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s


def _clean(text):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(text))


def _escape(text):
    return escape(_clean(text))


STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="%s">'
    '<fonts count="2">'
    '<font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/></font>'
    '</fonts>'
    '<fills count="2"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill></fills>'
    '<borders count="1"><border/></borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="3">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"'
    ' applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">'
    '<alignment vertical="top" wrapText="1"/></xf>'
    '</cellXfs>'
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
    '</styleSheet>' % MAIN)


def _sheet_xml(rows, widths, freeze=True):
    """Element order is fixed: dimension, sheetViews, sheetFormatPr, cols, sheetData, autoFilter."""
    last_col = col_letter(max(len(r) for r in rows) - 1) if rows else "A"
    n = len(rows)
    parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<worksheet xmlns="%s">' % MAIN,
             '<dimension ref="A1:%s%d"/>' % (last_col, max(n, 1))]
    if freeze:
        parts.append('<sheetViews><sheetView workbookViewId="0">'
                     '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft"'
                     ' state="frozen"/></sheetView></sheetViews>')
    parts.append('<sheetFormatPr defaultRowHeight="15"/>')
    if widths:
        parts.append("<cols>")
        for i, w in enumerate(widths):
            parts.append('<col min="%d" max="%d" width="%s" customWidth="1"/>'
                         % (i + 1, i + 1, w))
        parts.append("</cols>")
    parts.append("<sheetData>")
    for r_i, row in enumerate(rows, start=1):
        style = 1 if r_i == 1 else 2
        cells = []
        for c_i, val in enumerate(row):
            if val is None or val == "":
                continue
            cells.append(
                '<c r="%s%d" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
                % (col_letter(c_i), r_i, style, _escape(val)))
        parts.append('<row r="%d">%s</row>' % (r_i, "".join(cells)))
    parts.append("</sheetData>")
    if n:
        parts.append('<autoFilter ref="A1:%s%d"/>' % (last_col, n))
    parts.append("</worksheet>")
    return "".join(parts)


def write_xlsx(path, sheets):
    """sheets: list of (name, rows, widths). Rows are lists of strings."""
    sheets = [(nm, rows, widths if len(widths) == len(rows[0]) else widths)
              for nm, rows, widths in sheets]

    ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
          '<Types xmlns="%s">' % CT,
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
          '<Default Extension="xml" ContentType="application/xml"/>',
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
          '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
    for i in range(1, len(sheets) + 1):
        ct.append('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % i)
    ct.append("</Types>")

    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="%s">'
            '<Relationship Id="rId1" Type="%s/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>' % (PKG_REL, REL))

    wb_sheets = "".join('<sheet name="%s" sheetId="%d" r:id="rId%d"/>'
                        % (_escape(nm), i + 1, i + 1)
                        for i, (nm, _, _) in enumerate(sheets))
    workbook = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="%s" xmlns:r="%s"><sheets>%s</sheets></workbook>'
                % (MAIN, REL, wb_sheets))

    wb_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
               '<Relationships xmlns="%s">' % PKG_REL]
    for i in range(1, len(sheets) + 1):
        wb_rels.append('<Relationship Id="rId%d" Type="%s/worksheet" Target="worksheets/sheet%d.xml"/>'
                       % (i, REL, i))
    wb_rels.append('<Relationship Id="rId%d" Type="%s/styles" Target="styles.xml"/>'
                   % (len(sheets) + 1, REL))
    wb_rels.append("</Relationships>")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "".join(ct))
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", "".join(wb_rels))
        z.writestr("xl/styles.xml", STYLES)
        for i, (_, rows, widths) in enumerate(sheets, start=1):
            z.writestr("xl/worksheets/sheet%d.xml" % i, _sheet_xml(rows, widths))
