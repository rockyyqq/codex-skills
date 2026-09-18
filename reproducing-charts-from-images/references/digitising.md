# Digitising a chart image

Prefer an automatic route (`scripts/digitize_chart.py`) and fall back to targeted
probes. Either way, expect the recovered values to land within roughly 0.01-0.06 of
a scale unit, and cross-check against any statistic the user already supplied.

## What the script does

1. Background = the image's most common colour.
2. Gridlines = columns where that stroke colour covers most of the column. Coverage
   is used rather than run length because plotted bars cut each gridline into
   pieces, so a heavily crossed gridline has no long run left.
3. Plot area = union of the long runs in those columns. Short runs of the same
   colour elsewhere (a 2px rule lower down a slide, a stray mark) are ignored.
4. Calibration = `value = tick0 + (x - x_at_tick0) / pixels_per_tick`, from the
   first and last gridline. Values are never read off axis labels by eye.
5. Rows = horizontal bands of chart ink, where the band window is kept narrower
   than the row pitch.
6. Each row's two marker centres = peak of the vertical-extent profile near each
   end, so a marker is found by its silhouette rather than by colour alone.
7. `before` vs `after` comes from the interior colour: a white interior is the
   hollow marker. Never assume the hollow marker is the left one.

Run it, then **open the `_detected.png` overlay** and confirm the crosses sit on the
markers. Numbers without that check are not evidence.

## Failure modes to check first

| Symptom | Cause | Fix |
|---|---|---|
| Every row counts as ink; one giant row band | Antialiasing halos around gridlines pass the ink test | Keep the background-to-gridline blend filter (`--blend-tol`); widen it if rows still merge |
| Marker centres biased ~0.03 low | Mask includes bars but not the hollow markers' lighter ring, so the extent stops at the bar cap | Ensure the ring colour survives colour clustering; check `series_colours` in the JSON |
| Values off by a whole row | Measurement window taller than the row pitch, so neighbouring rows leak into the extent profile | Window must be ~pitch/2 - 1 |
| Extra rows at the end | The legend or a footer rule sits inside the estimated plot area | Confirm plot_area top/bottom in the JSON against the image |
| One item's difference has the wrong sign | Hollow marker assumed to be on the left | Read `hollow_side`; a score that fell draws its solid marker on the left |
| Differences systematically ~2x the true value | Two near-identical series colours merged, or a doubled axis | Check `pixels_per_tick` against tick spacing in the image |

## Cross-checking

The strongest signal that an extraction is right is agreement with a number the user
already has. Compare the recovered `before - after` against a reported mean
difference, or the recovered totals against a printed sum. Errors of a few
hundredths are normal; a mismatch that grows with bar length means the calibration
is wrong, and a constant offset means the marker centre is misplaced.

Then say in the handover which values came from the image and which from the
analysis output, and offer to substitute exact values. See the anchoring rule in
`SKILL.md`.
