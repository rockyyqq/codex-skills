# XLSX mechanics

The analysis is rarely what goes wrong. These are the traps that cost real time.

## No spreadsheet library available

`import openpyxl` failing is normal, and `pip install` may time out with no output
at all (no network, or a blocked index). Do not burn a long timeout on it. An
.xlsx is a ZIP of XML parts and the standard library is enough:

- **Reading** - open with `zipfile`, parse with `xml.etree.ElementTree`.
- **Writing** - emit the minimal part set and zip it.

A minimal single-format workbook needs exactly these parts:

```
[Content_Types].xml
_rels/.rels
xl/workbook.xml
xl/_rels/workbook.xml.rels
xl/styles.xml
xl/worksheets/sheet1.xml   (and sheet2.xml, ... per sheet)
```

Element order inside a worksheet is fixed and Excel is strict about it:

```
dimension, sheetViews, sheetFormatPr, cols, sheetData, autoFilter
```

Putting `cols` after `sheetData` produces a file that looks fine to a parser and
triggers a repair prompt in Excel.

Use **inline strings** (`<c r="A1" t="inlineStr"><is><t>text</t></is></c>`) and
skip `sharedStrings.xml` entirely. Escape `&`, `<`, `>`; strip control characters
below `0x20` (except tab, newline, carriage return) or the XML is invalid. Add
`xml:space="preserve"` to every `<t>` or leading and trailing spaces are lost -
which silently breaks byte-identical quote checks.

`scripts/xlsx_io.py` implements reader and writer.

### Reading: inline strings versus shared strings

A workbook written by Excel uses `xl/sharedStrings.xml`; one written by a script
often uses inline strings. A reader that handles only one silently returns empty
cells on the other. Handle both, plus numeric `<v>` values.

```python
if t == "inlineStr":
    val = "".join(x.text or "" for x in cell.iter("{ns}t"))
elif t == "s":
    val = shared[int(v.text)]
```

## Cloud-placeholder files that refuse to open

In a OneDrive or Dropbox folder, a file may be **dehydrated** - present with a
size and timestamp, but not actually on disk (`Attributes` shows `ReparsePoint`).

Symptoms: `PermissionError: [Errno 13] Permission denied` at the `open`, from
`zipfile.ZipFile`, PowerShell, and Python alike. It is easy to misread as a
sandbox or policy denial. It is not, and **raising the sandbox level does not fix
it** - the read fails at the OS level too.

Diagnose:

```powershell
Get-ChildItem *.xlsx | Select-Object Name, Length, Attributes
```

`ReparsePoint` alongside `Archive` is the tell.

Fix - force hydration by copying, then read the copy:

```powershell
Copy-Item $file 'work\hydrated_copy.xlsx' -Force
```

Verify the copy is the same artifact (same part count and names) before using it,
and **say in the deliverable and to the user that a copy was used**. A file you
just wrote in the same folder will read fine, which is why this only bites when
revisiting an earlier session's output.

## Verifying the delivered workbook

Three levels, cheapest first:

1. **Re-read it with your own reader** and re-run the content assertions. Catches
   truncation and encoding loss.
2. **Parse every part as XML** and check that every `Override` in
   `[Content_Types].xml` and every relationship target resolves to a part that
   exists. Catches a part that was never written.
3. **Open it in the real application.** On Windows with Office installed, Excel
   via COM is the definitive check - it applies the same validation that produces
   the repair prompt.

```powershell
$xl = New-Object -ComObject Excel.Application
try {
  $xl.Visible = $false; $xl.DisplayAlerts = $false
  $wb = $xl.Workbooks.Open($path)          # throws if Excel would prompt to repair
  $wb.Worksheets | ForEach-Object { "$($_.Name): $($_.UsedRange.Rows.Count)" }
  $wb.Close($false)
} finally { $xl.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) }
```

Always `Quit()` and release in a `finally`. A leaked Excel process holds the file
locked and every later write fails with a permission error that looks like the
cloud-placeholder problem but is not.

Reading cells back through COM also confirms what a human will actually see,
which is a different question from what your reader parsed.

## Console encoding is not file corruption

Printing non-ASCII text to a Windows console shows `??` or mojibake. This is the
console code page, not the file. Do not "fix" it and do not conclude the data is
damaged.

Decide it in code, where nothing round-trips through a console:

```python
print("mojibake" if src_text != out_text else "ok")
```

If you must see the characters, write them to a UTF-8 file and read that.

## Loose ends worth checking

- **Frozen header and autofilter** are cheap and make a 120-row sheet usable.
  `<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>`.
- **Column widths** must be set, or every quotation column opens as a sliver.
- **Leave the source file untouched.** Copy it, or write a new file. Never
  overwrite the input in place.
