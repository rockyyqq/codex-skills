# OfficeCLI — PowerPoint (.pptx)

Paths are 1-based: `/slide[1]`, `/slide[1]/shape[2]`, `/slide[1]/tbl[1]`, `/slideMaster[1]`, `/slideLayout[1]`.
`officecli help pptx set <element>` for authoritative properties.

## Elements

| Element | Notable capabilities |
|---|---|
| slide | header/footer/date/slide-number toggles, hidden |
| shape | pattern fill, blur effect, hyperlink tooltip + slide-jump links, **highlight color** on runs, arrow alias, `effective.X` + `effective.X.src` (inherited-value tracing) |
| picture | PNG / JPG / GIF / SVG; fill modes stretch / contain / cover / tile; brightness, contrast, glow, shadow; rotation; link + tooltip |
| table | built-in PowerPoint style catalogue; virtual `/col[C]` get + swap/copyFrom; row/col move/copyFrom |
| chart | pieOfPie, barOfPie, per-attribute axis/gridline setters, series add/remove with theme palette, `anchor=x,y,w,h` |
| equation | **LaTeX input** |
| diagram | **mermaid flowchart / sequence → native editable shapes**, or any mermaid type as full-fidelity PNG |
| animation | 15 emphasis + 16 exit template-backed presets, multi-effect chains, motion-path presets, repeat/restart/autoReverse, chart animations + `chartBuild` |
| transition | morph + p14 + 12 PowerPoint 2013+ presets |
| 3D model | `.glb`, combined `rotation=ax,ay,az` |
| zoom | slide zoom |
| connector | `from`/`to` accept a full `/slide[N]/shape[@name=Foo]` path |
| group | link + tooltip; get/query/add/remove all descend into groups |
| notes | RTL, lang |
| comment | RTL; legacy + modern p188 threaded round-trip |
| video / audio | loop, autoStart |
| placeholder | add/set by phType |
| theme | `slideMaster` / `slideLayout` typed add/set/remove |
| SmartArt | round-trip via add-part + raw-set |
| OLE object | embedded objects |

## Rendering — the reason to reach for OfficeCLI

```powershell
officecli view deck.pptx screenshot -o deck.png --page 1-8
officecli view deck.pptx screenshot -o deck.png          # all slides
officecli view deck.pptx html -o deck.html               # standalone, assets inlined
officecli watch deck.pptx                                # live preview, http://localhost:26315
```

Per-page PNGs come from the built-in HTML rendering engine piped through a headless browser — **no Office, no display, works in CI/headless**. This is what makes the *render → look → fix* loop possible for decks and posters: you can actually see whether a title overflows or two shapes overlap instead of guessing from the DOM.

Where this integrates with existing skills in this workspace:

- `poster-review` requires **independent verification of the rendered PPTX** — a rendered PNG inspected by someone other than the author satisfies that; `view screenshot` is how you produce it, and `view issues` gives a machine-checkable complement.
- `reproducing-charts-from-images` / `reproducing charts` workflows benefit from comparing a re-rendered slide against the source image.

Report what you actually saw in the render, page by page. A render produced but never opened is not verification.

## Common commands

```powershell
officecli create deck.pptx
officecli add deck.pptx / --type slide --prop title="Q4 Report" --prop background=1A1A2E
officecli add deck.pptx '/slide[1]' --type shape `
  --prop text="Revenue grew 25%" --prop x=2cm --prop y=5cm `
  --prop font=Arial --prop size=24 --prop color=FFFFFF
officecli view deck.pptx outline
officecli view deck.pptx issues --json
officecli get deck.pptx '/slide[1]/shape[1]' --json
officecli get deck.pptx / --depth 2 --json
officecli validate deck.pptx
officecli set deck.pptx '/slide[1]/shape[1]' --prop fill=FF0000
```
