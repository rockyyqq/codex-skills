# Rebuilding the look

Measure the reference instead of guessing: the palette, the geometry and the type
sizes are all recoverable in a few lines of numpy/Pillow, and measuring beats
eyeballing every time.

## Measure these before drawing

```python
from collections import Counter
import numpy as np
from PIL import Image

a = np.asarray(Image.open("reference.png").convert("RGB")).astype(int)

# palette: dominant colours tell you background, series colours, gridline, text
Counter(map(tuple, a.reshape(-1, 3))).most_common(12)

# vertical gridlines, then row pitch, then text bounding boxes
colour = np.array([232, 220, 209])                 # the gridline you just found
cols = [x for x in range(a.shape[1]) if (np.abs(a[:, x] - colour).sum(axis=1) < 40).mean() > 0.3]
rows = [y for y in range(a.shape[0]) if (np.abs(a[y] - colour).sum(axis=1) < 40).any()]
```

Useful quantities and how to read them off:

- **Gridline x positions** give the value scale: `pixels_per_unit = (x_last - x_first) / (v_last - v_first)`.
- **Row pitch** = median gap between band centres. Draw the rebuild with the same
  pitch so the density of the figure matches.
- **Text sizes** should be matched by width, not by height: render the string at
  100px, measure its width, then `size = 100 * target_width / width_100`. Bounding
  boxes include ascenders, descenders and neighbouring rows, so width is the
  reliable signal.
- **Marker radii** = half the vertical extent at the marker's centre column. Hollow
  and solid markers in the same figure are often *different* sizes; measure both.
- **Bar thickness** = the median vertical extent of the connecting bars.

Aim to reproduce the reference's own pixel grid (for example 1168x544) and scale up
at draw time; that keeps every measured constant meaningful and gives a print-ready
render in one pass.

## Structure the code so regenerating is cheap

```
scripts/
  <data>.py          # one module: every number, one ordering, no layout
  render_figure.py   # the picture, reads the data module
  build_workbook.py  # the spreadsheet, reads the same module
```

The data module is the only place a number or an ordering exists. When the user
re-sorts, re-colours or re-derives anything, change it there and re-run every
consumer; never hand-edit one artifact.

## Verification

- Render, then look at the actual image (or the actual slide) - a successful exit
  code is not a check.
- Compare against the reference side by side, and where the design matters, blend
  the two. A 50% blend makes offsets, wrong bar lengths and misplaced labels jump
  out in a way two separate images do not.
- Re-verify after any ordering change: the numbers stay correct while the row
  labels quietly shift out of step with the table beside them.

## Getting an editable artifact

Ask what the user actually needs before building an Office-native object:

- **Image (PNG/PDF)** reproduces any design exactly and drops straight into Word or
  a slide. Usually the right answer for a paper.
- **PowerPoint shapes** give a genuinely editable version of an unusual chart:
  each bar, marker and label is a shape that can be nudged and restyled.
- **Excel-native** is only better when the user will re-enter data. Many chart
  types do not exist natively - a dumbbell chart has to be faked with a scatter
  chart plus a connector series and a hidden numeric axis, and a native chart
  cannot be visually verified without opening Excel. Say so, rather than shipping
  a workaround that may render wrong.

If numbers must live in a workbook, ship the table as data, the picture as the
figure, and keep the source statistics on their own sheet so every number can be
traced back.
