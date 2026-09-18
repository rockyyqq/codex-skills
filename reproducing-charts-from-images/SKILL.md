---
name: reproducing-charts-from-images
description: Use when someone supplies a chart, figure or graph as an image (screenshot, slide, pasted picture) and wants it recreated, restyled, reordered, exported to Excel/PowerPoint, or wants the underlying numbers pulled back out - including "make me this same graph".
metadata:
  short-description: Rebuild a chart from a reference image
---

# Reproducing Charts From Images

A reference image is a data source and a design spec at once. Recover both by
measuring pixels, never by eyeballing values off the axis.

## When to use

- "Generate this same graph", "match my figure", "here's a screenshot of my chart".
- The numbers exist only as a picture (pasted from SPSS, Excel, R, matplotlib, a slide).
- A figure must be restyled, reordered or moved into Excel/Word/PowerPoint while
  keeping its look.

Not for charts whose data is already in a file - read the file.

`scripts/digitize_chart.py` needs numpy and Pillow; use the workspace runtime Python
if the default interpreter lacks them.

```bash
python scripts/digitize_chart.py chart.png --ticks 5,6,7,8,9,10 --out values.json
```

## Workflow

1. **Recover the numbers** with the script, reading
   [references/digitising.md](references/digitising.md) for the failure modes.
2. **Cross-check against any statistic the user already gave you.** A mean
   difference, a total, a printed p-value: if the geometry disagrees with a known
   number, the measurement is wrong, not the number. Agreement within the printed
   precision is the signal that the extraction is sound.
3. **Recover the design** - palette, gridline positions, row pitch, type sizes - by
   measuring the reference, per [references/rebuilding.md](references/rebuilding.md).
4. **Keep one source of truth:** a single data module feeds the figure, the
   workbook, the table and the notes. No document restates a number that lives
   elsewhere.
5. **Render and look at it.** Compare against the reference, then open the output
   file. No exception raised is not verification.

## Invariants that bite

- **One ordering, applied everywhere.** Decide the row order once and let every
  artifact read it; when the user re-sorts, change it at the source and regenerate
  every consumer.
- **Recovered values are not free parameters.** Round to the source's precision and
  anchor each pair to the exact statistic the user reported. Say which numbers were
  measured from the image and which came from the analysis output, and offer to swap
  in exact values.
- **Sign and direction are data.** Which marker is "before" and which is "after"
  comes from the legend, not from left-to-right position; a score that fell draws
  its solid marker on the left.
- **Match the medium to the job.** Say when a chart type does not exist natively
  (a dumbbell chart in Excel) instead of shipping a workaround you cannot verify.

## Handing it to an independent verifier

When the figure carries numbers someone will act on, the check that counts is
independent re-derivation rather than a second read of the rebuilt picture.

- **Pass over:** the reference image, the rendered figure, the recovered values as
  JSON, the `_detected.png` overlay, and any outside statistic the values must match.
  That statistic is a source, not a conclusion - hand it over deliberately.
- **Withhold:** your measured values and your view of whether they are right.
- **A pass looks like:** values re-derived from the image by someone who has not seen
  the author's numbers; a sample also checked by eye against the source, so a
  systematic error in the measuring tool cannot pass as agreement; one row order
  across every artifact that lists the same rows; and the figure judged from its
  rendered output rather than its script.
- An overlay nobody opened is not evidence.

For who verifies, who judges the design, and how many roles the stakes justify, use
the `role-split` skill when it is available.
