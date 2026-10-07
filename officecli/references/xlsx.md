# OfficeCLI — Excel (.xlsx)

Paths: sheets by name (`/Sheet1`, `$Sheet1:A1`), cells as `A1`. Selectors support boolean `and`/`or` and row-by-column-name comparisons: `row[Salary>5000 and Region=EMEA]`.
`officecli help xlsx <command>` lists settable properties.

## Formula engine

350+ built-in functions are **evaluated automatically on write** — write `=SUM(A1:A2)`, then `get` the cell and the value is already computed. No round-trip through Excel to recalculate.

- Spilling dynamic arrays: `FILTER`, `SORT`, `UNIQUE`, `SEQUENCE`, `LET`, `LAMBDA`, `MAP` (auto `_xlfn.` prefix)
- Lookups: `VLOOKUP`, `XLOOKUP`, `INDEX`, `MATCH`
- Financial / bond: `XIRR`, `PRICE`, `YIELD`, `DURATION`, `COUPNUM`
- Statistical: distributions, `T.TEST`, `LINEST`, regression
- `OFFSET` / `INDIRECT`; defined-name formula bodies inlined at parse
- Formula references rewritten on row/column insert

**Caveat for this workspace:** the value is computed by OfficeCLI's own engine. If a downstream consumer depends on Excel's exact recalculation, verify against the bundled LibreOffice (`office-xlsx` skill) or pandas rather than trusting one engine.

## Pivot tables

Native OOXML pivot tables written from a source range in one command; the cache and definition land in the file, so Excel opens it already aggregated.

```powershell
officecli add sales.xlsx '/Sheet1' --type pivottable `
  --prop source='Data!A1:E10000' --prop rows='Region,Category' `
  --prop cols=Quarter --prop values='Revenue:sum,Units:avg' `
  --prop showDataAs=percentOfTotal
```

Supports multi-field rows/cols/filters, 10 aggregations, `showDataAs` modes, date grouping, calculated fields, persistent `labelFilter` / `topN`, sort, grand totals, subtotals, compact/outline/tabular layout, repeat item labels, cache copy-on-write with cross-pivot sharing.

## Other elements

| Element | Capabilities |
|---|---|
| cell | phonetic guide / furigana on add; `--shift left\|up` on remove; `shift=right\|down` on add |
| sheet | visible / hidden / veryHidden, print margins, `printTitleRows`/`printTitleCols`, RTL `sheetView`, cascade-aware rename, empty-cell bloat filter on open |
| table | structured tables |
| sort | sheet or range, multi-key, sidecar-aware |
| conditional formatting | rule-based |
| chart | incl. box-whisker, pareto (auto-sort + cumulative %), log axis |
| sparkline | in-cell |
| slicer | pivot slicers |
| named range | defined names |
| data validation | dropdowns, constraints |
| autofilter | filter ranges |
| picture | PNG / JPG / GIF / SVG, dual-representation fallback |
| shape | drawing shapes |
| comment | including RTL |
| OLE object | embedded objects |

Also: CSV / TSV import (`officecli import budget.xlsx "/Q1 Data" sales.csv --header`).

## Common commands

```powershell
officecli view budget.xlsx text --cols A,B,C --max-lines 50
officecli query sales.xlsx "row[Salary>5000]" --json
officecli add budget.xlsx / --type sheet --prop name="Q2 Data"
officecli add budget.xlsx '/Q2 Data' --type cell --prop ref=A1 --prop value="Revenue"
officecli batch budget.xlsx --input updates.json --json
officecli get budget.xlsx '/Sheet1/A1' --json
```
