# OfficeCLI — command reference

Source: <https://github.com/iOfficeAI/OfficeCLI> (Apache 2.0) and <https://officecli.ai/SKILL.md>.
Version this was written against: pre-1.1 (1.0.137-era flags).

## Command surface

| Command | Purpose | Notes |
|---|---|---|
| `create <f>` | blank `.docx` / `.xlsx` / `.pptx` | type from extension |
| `view <f> <mode>` | read | modes: `outline`, `text`, `annotated`, `stats` (`--page-count`), `issues`, `html`, `svg`, `screenshot`, `pdf` (plugin), `forms` (plugin) |
| `watch <f>` | live HTML preview | http://localhost:26315, auto-refresh on mutation |
| `get <f> <path>` | element + children | `--depth N`, `--json` |
| `query <f> <selector>` | CSS-like search | boolean `and`/`or`, `row[Salary>5000]`, `--find` |
| `set <f> <path>` | modify properties | `--find`/`--replace` |
| `add <f> <parent>` | add element | `--type`, `--prop`, `--from <path>` to clone |
| `remove` / `move` / `swap` | restructure | `move --to <parent> --index N` \| `--after` \| `--before` |
| `validate <f>` | OpenXML schema check | |
| `batch <f>` | many ops, one pass | stdin \| `--input` \| `--commands`; atomic by default; `--best-effort`, `--stop-on-error` |
| `dump <f> [path]` | serialize to replayable batch JSON | accepts a subtree (`/body/tbl[1]`, `/Sheet1`) |
| `merge <tpl> <out>` | replace `{{key}}` with JSON | spans paragraphs, tables, shapes, headers/footers, chart titles |
| `refresh <f>` | recalc TOC page numbers / `PAGE` / cross-refs | docx; Word backend on Windows, headless-HTML fallback |
| `open` / `save` / `close` | resident mode | see flush model below |
| `raw` / `raw-set` / `add-part` | L3 XPath XML access | universal fallback |
| `mcp <client>` | register MCP server | `claude` \| `cursor` \| `vscode` \| `lmstudio`; `mcp list` |
| `install` | binary + skills + MCP | `all`, `claude`, `cursor`, … |
| `config` | get/set config | `~/.officecli/config.json` |
| `help <format> <cmd> [element]` | built-in help | e.g. `officecli help pptx set shape` |
| `load_skill` | print embedded SKILL.md | no install needed |

## Units, colors, sizes

| Type | Accepted | Examples |
|---|---|---|
| Dimensions | cm, in, pt, px, raw EMU | `2cm`, `1in`, `72pt`, `96px`, `914400` |
| Colors | hex, named, rgb, theme | `#FF0000`, `FF0000`, `red`, `rgb(255,0,0)`, `accent1` |
| Font sizes | bare number or pt | `14`, `14pt`, `10.5pt` |
| Spacing | pt, cm, in, multiplier | `12pt`, `0.5cm`, `1.5x`, `150%` |

## JSON shapes

`get --json`:
```json
{"tag":"shape","path":"/slide[1]/shape[1]","attributes":{"name":"TextBox 1","text":"Hello"}}
```

`query --json`: array of `{tag, path, attributes}`.

Error envelope:
```json
{"success":false,"error":{"error":"Slide 50 not found (total: 8)","code":"not_found","suggestion":"Valid Slide index range: 1-8"}}
```

Error codes: `not_found`, `invalid_value`, `unsupported_property`, `invalid_path`, `unsupported_type`, `missing_property`, `file_not_found`, `file_locked`, `invalid_selector`. Property names are auto-corrected with a closest-match suggestion.

Mutation confirmation: `{"success":true,"path":"/slide[1]/shape[1]"}`.

Recovery pattern — inspect children, then retry:
```powershell
officecli get report.docx /body/p[99] --json   # not_found + suggestion
officecli get report.docx /body --depth 1 --json   # pick a valid path
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | operation landed |
| 1 | did not land (process or business failure; envelope carries `error`) |
| 2 | ran with caveats — `unsupported_property` dropped or validator warning. Covers both `success:true` (landed with warning) and `success:false` (nothing applied) |

**Always read the envelope's `success` and `warnings[]`; never infer outcome from the exit code alone.**

## Flush model (resident mode)

A live resident defers disk writes; it auto-flushes when idle (adaptive 2–10s, scaled to save cost). Control it with `OFFICECLI_RESIDENT_FLUSH`:

- `each` — every mutation on disk before the command returns, resident stays warm. Use this in any pipeline where a foreign reader runs after each command.
- `auto` — default adaptive behavior.
- fixed delay / `off` — explicit, or disable auto-flush (then `save` is mandatory).

`save` flushes and keeps the resident warm; `close` flushes and releases. OfficeCLI's own reads always see latest edits; python-docx/openpyxl/openpyxl-class readers, LibreOffice, renderers and uploads do not.

## Batch semantics

- Default is **atomic**: any failed item rolls back the whole batch.
- `--best-effort` keeps whatever succeeded (pre-1.0.137 behavior).
- `--stop-on-error` aborts at the first failure (still rolls back unless combined with `--best-effort`).

## SDKs

```python
# pip install officecli-sdk
import officecli
with officecli.create("deck.pptx") as doc:
    doc.send({"command": "add", "parent": "/", "type": "slide"})
    print(doc.send({"command": "get", "path": "/slide[1]"}))
```

```javascript
// npm install @officecli/sdk
const oc = require("@officecli/sdk");
const doc = await oc.create("deck.pptx");
await doc.send({ command: "add", parent: "/", type: "slide" });
await doc.close();
```

Both auto-provision the native CLI when missing and announce the install.

## Plugins

`plugins` lists / inspects / lints installed plugins; extension kinds are dump-reader, exporter (e.g. `.pdf` export) and format-handler (e.g. `.doc`, `.hwpx`, `view forms`).
