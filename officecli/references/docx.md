# OfficeCLI — Word (.docx)

Element paths are 1-based (`/body/p[1]/r[1]`, `/body/tbl[1]`). Selectors support `:contains()`, `:has()`, attribute matches and booleans.
Use `officecli help docx <command>` for the authoritative property list before guessing.

## Elements

| Element | Notable capabilities |
|---|---|
| paragraph | `framePr`, tab shorthand, char-based indents |
| run | `underline.color`, `position` (half-points) |
| table | virtual column ops (add/remove/move/copyFrom), `hMerge` |
| style | paragraph/character style definition and application |
| textbox / shape | rotation, `textDirection` (`eaVert`/`vert270`), gradient, shadow, opacity |
| picture | PNG / JPG / GIF / SVG |
| equation | **LaTeX input** |
| diagram | **mermaid → native editable shapes**, or any mermaid type as full-fidelity PNG |
| chart | native Word charts |
| header / footer | per-section |
| footnote / comment / bookmark / watermark | |
| TOC | plus `refresh` to recalculate page numbers |
| section | page setup, columns |
| hyperlink | internal and external |
| formfield | legacy form fields |
| SDT | content controls |
| field | 22 zero-param types + MERGEFIELD / REF / PAGEREF / SEQ / STYLEREF / DOCPROPERTY / IF |
| revision | tracked changes: `revision.type=ins\|del\|format\|moveFrom\|moveTo`, `revision.action=accept\|reject`, per-target `/revision[@author=Alice]`, tracked Find & Replace |
| OLE object | embedded objects |
| document properties | metadata, page background color |

## i18n and RTL

- Per-script font slots and per-script BCP-47 tags: `lang.latin` / `lang.ea` / `lang.cs`.
- Complex-script bold / italic / size.
- `direction=rtl` cascades through paragraph → run → section → table → style → header/footer → docDefaults.
- `rtlGutter`, `pgBorders` shorthand.
- Locale-aware page numbering for Hindi / Arabic / Thai / CJK.
- `create --locale ar-SA` auto-enables RTL.

Relevant for any Chinese-language document in this workspace: set the East Asian font slot and `lang.ea` explicitly, otherwise the Latin font slot is used and CJK glyphs fall back unpredictably.

## Common commands

```powershell
officecli view report.docx annotated
officecli view report.docx issues --json
officecli query report.docx "paragraph[style=Heading1]" --json
officecli set report.docx /body/p[1]/r[1] --prop text="New Title"
officecli set report.docx /body/p[1]/r[1] --prop bold=true
officecli add report.docx /body --type paragraph --prop text="Added"
officecli move report.docx /body/p[5] --to /body --index 1
officecli refresh report.docx          # TOC / PAGE / cross-refs
officecli raw report.docx document     # L3 XML fallback
```

## i18n/RTL source

<https://github.com/iOfficeAI/OfficeCLI/wiki/i18n>
