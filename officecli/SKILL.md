---
name: officecli
description: Use for Office document work in this workspace - any create, read, edit, check, render or deliver task on Word (.docx), Excel (.xlsx) or PowerPoint (.pptx). Wraps OfficeCLI and routes to the bundled office-docx / office-pptx / office-xlsx skills, first-line for ordinary authoring and conversion. Use it when the file must be seen, not only edited - PNG rendering, screenshots, layout QA, headless CLI or JSON work, mermaid to native shapes, LaTeX equations, template merge, issue checks.
---

# OfficeCLI (second Office toolchain)

OfficeCLI is a single self-contained binary that creates, reads, edits, validates and **renders** `.docx` / `.xlsx` / `.pptx` with no Microsoft Office installed. It is a CLI, not a library.

## Toolchain routing — decide this first

| Need | Use |
|---|---|
| Ordinary create / read / edit / convert an Office file | the matching `office-*` skill (bundled LibreOffice) |
| **See** the result — per-page PNG, layout QA | **OfficeCLI** `view screenshot` |
| Text overflow, missing alt text, formula errors | **OfficeCLI** `view issues` |
| Mermaid diagram as native editable shapes | **OfficeCLI** |
| LaTeX equation as a native equation | **OfficeCLI** |
| Fill `{{key}}` placeholders across many files | **OfficeCLI** `merge` |
| Headless / CI, structured JSON, batch edits | **OfficeCLI** |
| Reuse an existing human-made doc as a blueprint | **OfficeCLI** `dump` → `batch` |

The two toolchains coexist; neither rewrites the other's workflow. **Never** describe OfficeCLI as replacing the bundled LibreOffice path unless the user explicitly opts out of it.

## Step 0 — availability

```powershell
officecli --version          # on PATH?
Test-Path "$env:USERPROFILE\.officecli\officecli.exe"
```

If neither, install once (ask the user first — it writes outside the workspace and lands on PATH):

```powershell
# Windows; script execution policy may block this — retry with the bypass
irm https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.ps1 | iex
# fallback if the machine forbids script execution:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

Verify with `officecli --version` before promising any document work. If the shell cannot run at all, say so and stop — do not fake a rendering result.

## Core commands

```powershell
officecli create deck.pptx
officecli view deck.pptx outline            # text | annotated | stats | issues
officecli view deck.pptx screenshot -o out.png --page 1-8   # per-page PNG — the "eyes"
officecli view deck.pptx html -o out.html   # standalone, assets inlined
officecli watch deck.pptx                   # http://localhost:26315 live preview
officecli get deck.pptx '/slide[1]' --depth 2 --json
officecli query report.docx "run:contains(TODO)" --json
officecli set deck.pptx '/slide[1]/shape[1]' --prop text="Q4 Results"
officecli add deck.pptx / --type slide --prop title="Details"
officecli remove | move | swap <file> <path> ...
officecli validate deck.pptx
officecli batch deck.pptx --commands '[{"op":"set","path":"/slide[1]/shape[1]","props":{"text":"Hi"}}]'
officecli merge template.docx out.docx --data '{"client":"Acme"}'
officecli dump existing.pptx -o blueprint.json
officecli help pptx set shape               # built-in help beats guessing property names
```

Addressing is 1-based element paths (`/slide[1]/shape[2]`), **not** XPath — that is the `raw` / `raw-set` layer only.

## Serialization — the rule that breaks pipelines

A live resident defers writes to disk. **Before any non-OfficeCLI program reads the file** (`python-docx`, openpyxl, LibreOffice, a renderer, an upload):

```powershell
officecli save report.docx      # flush, keep resident warm
officecli close report.docx     # flush + release
$env:OFFICECLI_RESIDENT_FLUSH="each"   # or flush on every mutation
```

OfficeCLI's own `get` / `query` / `view` always see the latest edits; only foreign readers need the flush.

## Honest reporting rules

- Exit `0` = landed, `1` = failed, `2` = ran with caveats (a property was dropped, or nothing applied). **Read `success` in the `--json` envelope**, not the exit code alone.
- Report rendering evidence as observed: which file, which page, what you saw. A render you did not actually open is not verification.

## References

- [references/commands.md](references/commands.md) — full command surface, JSON shapes, error codes
- [references/docx.md](references/docx.md) — Word element/property reference
- [references/xlsx.md](references/xlsx.md) — Excel element/property reference
- [references/pptx.md](references/pptx.md) — PowerPoint element/property reference
