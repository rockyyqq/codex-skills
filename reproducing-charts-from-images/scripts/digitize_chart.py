#!/usr/bin/env python3
"""Recover plotted values from a chart image by measuring pixels.

Works for charts drawn as a marker pair joined by a bar (dumbbell, range,
connect-the-dots) and for any single-marker series.  The image is calibrated from
its own vertical gridlines, so no axis guessing is involved.

    python digitize_chart.py chart.png --ticks 5,6,7,8,9,10 --out values.json

Writes JSON plus a `_detected.png` overlay marking every marker centre it found.
Open that overlay and check the crosses sit on the markers before trusting the
numbers - that visual check is the verification step, not an optional extra.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def modal_colour(a: np.ndarray) -> np.ndarray:
    """Most common colour in the image: normally the plot background."""
    colours, counts = np.unique(a.reshape(-1, 3), axis=0, return_counts=True)
    return colours[counts.argmax()]


def longest_column_run(mask: np.ndarray) -> int:
    best = 0
    for x in range(mask.shape[1]):
        column = mask[:, x]
        if not column.any():
            continue
        edges = np.diff(np.concatenate(([False], column, [False])).astype(np.int8))
        starts, ends = np.where(edges == 1)[0], np.where(edges == -1)[0]
        best = max(best, int((ends - starts).max()))
    return best


def column_runs(column: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous True runs in a boolean column, as (start, end_exclusive)."""
    edges = np.diff(np.concatenate(([False], column, [False])).astype(np.int8))
    starts, ends = np.where(edges == 1)[0], np.where(edges == -1)[0]
    return list(zip(starts.tolist(), ends.tolist()))


def distance_to_segment(pixels: np.ndarray, start: np.ndarray, end: np.ndarray) -> np.ndarray:
    """L1 distance from each pixel to the line segment start-end.

    Antialiased edges are blends between a stroke colour and whatever sits behind
    it, so they lie on such a segment.  Filtering on this distance removes halos
    around thin gridlines, which otherwise make every row look like chart ink.
    """
    direction = (end - start).astype(float)
    norm = float(direction @ direction) or 1.0
    offset = pixels - start
    t = np.clip((offset @ direction) / norm, 0.0, 1.0)[:, None]
    nearest = start + t * direction
    return np.abs(pixels - nearest).sum(axis=1)


def gridline_colour(a: np.ndarray, bg: np.ndarray, tol: int, min_fraction: float = 0.4):
    """The stroke colour of the vertical gridlines, found by its long column runs."""
    non_bg = np.abs(a - bg).sum(axis=2) > tol
    if not non_bg.any():
        return None
    colours, counts = np.unique(a[non_bg].reshape(-1, 3), axis=0, return_counts=True)
    for idx in np.argsort(-counts)[:40]:
        colour = colours[idx]
        mask = np.abs(a - colour).sum(axis=2) <= tol
        if longest_column_run(mask) > min_fraction * a.shape[0]:
            return colour
    return None


def find_gridlines(a: np.ndarray, colour: np.ndarray, tol: int) -> tuple[list[float], int, int]:
    """Gridline x centres plus the plot's top and bottom rows."""
    mask = np.abs(a - colour).sum(axis=2) <= tol
    height = a.shape[0]
    # A gridline covers most of its column; bars, text and rules do not.  Total
    # coverage is immune to the bars that cut each gridline into short pieces.
    threshold = max(20, int(0.3 * height))
    columns = [x for x in range(a.shape[1]) if mask[:, x].sum() >= threshold]
    if not columns:
        return [], 0, 0

    groups: list[list[int]] = []
    for x in columns:
        if groups and x - groups[-1][-1] <= 2:
            groups[-1].append(x)
        else:
            groups.append([x])
    centres = [float(np.mean(g)) for g in groups]
    if not centres:
        return [], 0, 0

    # Plot height = union of the long runs in those columns.  Short runs of the
    # same colour (a 2px rule further down the slide, for instance) must not
    # stretch the plot area over decorative furniture.
    run_starts, run_ends = [], []
    for x in columns:
        for start, end in column_runs(mask[:, x]):
            if end - start >= 15:
                run_starts.append(start)
                run_ends.append(end)
    if not run_starts:
        return [], 0, 0
    top, bottom = int(min(run_starts)), int(max(run_ends)) - 1
    return centres, top, bottom


def ink_mask(a: np.ndarray, bg: np.ndarray, grid: np.ndarray, tol: int, blend_tol: int) -> np.ndarray:
    """Chart ink: not background, and not a blend between background and gridline."""
    flat = a.reshape(-1, 3)
    blends = distance_to_segment(flat, bg, grid) <= blend_tol
    ink = (np.abs(flat - bg).sum(axis=1) > tol) & ~blends
    return ink.reshape(a.shape[:2])


def series_colours(a: np.ndarray, ink: np.ndarray, plot: tuple, min_pixels: int = 60) -> list[np.ndarray]:
    top, bottom, left, right = plot
    window = ink[top : bottom + 1, left : right + 1]
    patch = a[top : bottom + 1, left : right + 1][window]
    if patch.size == 0:
        return []
    patch = patch[patch.min(axis=1) < 240]  # drop white marker interiors
    if patch.size == 0:
        return []
    colours, counts = np.unique((patch // 16) * 16, axis=0, return_counts=True)
    order = np.argsort(-counts)
    return [colours[i] for i in order[:8] if counts[i] >= min_pixels]


def row_bands(mark: np.ndarray, top: int, bottom: int, min_gap: int) -> list[tuple[int, int]]:
    bands: list[list[int]] = []
    for y in range(top, bottom + 1):
        if not mark[y].any():
            continue
        if bands and y - bands[-1][-1] <= min_gap:
            bands[-1].append(y)
        else:
            bands.append([y])
    return [(b[0], b[-1]) for b in bands]


def marker_at(strip: np.ndarray, yc: int, x_from: int, x_to: int, a: np.ndarray) -> dict:
    """Centre column, radius and fill of the marker at one end of a row."""
    x_from, x_to = max(0, int(x_from)), min(strip.shape[1], int(x_to))
    span = np.zeros(strip.shape[1])
    for x in range(x_from, x_to):
        ys = np.where(strip[:, x])[0]
        if len(ys):
            span[x] = ys.max() - ys.min() + 1
    window = span[x_from:x_to]
    if not window.any():
        return {"x": None, "radius": 0.0, "hollow": None}
    peak = int(np.argmax(window)) + x_from
    return {
        "x": peak,
        "radius": float(span[peak]) / 2.0,
        "hollow": bool(a[yc, peak].min() > 235),  # white interior
    }


def digitize(path: Path, ticks: list[float], tol: int, blend_tol: int) -> dict:
    image = Image.open(path).convert("RGB")
    a = np.asarray(image).astype(int)
    bg = modal_colour(a)
    grid = gridline_colour(a, bg, tol)
    if grid is None:
        raise SystemExit("no gridlines found; is this a chart image with an axis?")

    centres, top, bottom = find_gridlines(a, grid, tol)
    if len(centres) < 2:
        raise SystemExit("fewer than two gridlines found; cannot calibrate the axis")
    if len(centres) != len(ticks):
        print(
            f"warning: {len(centres)} gridlines detected vs {len(ticks)} tick values given",
            file=sys.stderr,
        )
    used = min(len(centres), len(ticks))
    first_x, last_x = centres[0], centres[used - 1]
    px_per_tick = (last_x - first_x) / (ticks[used - 1] - ticks[0])

    left = max(0, int(first_x - 0.6 * px_per_tick))
    right = min(a.shape[1] - 1, int(last_x + 0.6 * px_per_tick))
    plot = (top, bottom, left, right)
    ink = ink_mask(a, bg, grid, tol, blend_tol)

    series = series_colours(a, ink, plot)
    if not series:
        raise SystemExit("no series colours found inside the plot area")
    mark = np.zeros(a.shape[:2], dtype=bool)
    for colour in series:
        mark |= np.abs(a - colour).sum(axis=2) <= tol
    mark[:top] = False
    mark[bottom + 1 :] = False
    mark[:, :left] = False
    mark[:, right + 1 :] = False

    bands = row_bands(mark, top, bottom, min_gap=2)
    centres_y = [int(round((b[0] + b[-1]) / 2.0)) for b in bands]
    gaps = np.diff(centres_y)
    pitch = float(np.median(gaps)) if len(gaps) else float(bottom - top)
    half = max(4, int(pitch / 2) - 1)  # keep the window clear of neighbouring rows

    rows = []
    for yc in centres_y:
        strip = mark[yc - half : yc + half + 1]
        columns = np.where(strip.any(axis=0))[0]
        if len(columns) == 0:
            continue
        xmin, xmax = int(columns.min()), int(columns.max())
        width = int(min(24, max(10, (xmax - xmin) * 0.4)))
        window = a[yc - half : yc + half + 1]
        left_marker = marker_at(strip, strip.shape[0] // 2, xmin, xmin + width, window)
        right_marker = marker_at(strip, strip.shape[0] // 2, xmax - width, xmax + 1, window)
        if left_marker["x"] is None or right_marker["x"] is None:
            continue

        def to_value(x: float) -> float:
            return ticks[0] + (x - first_x) / px_per_tick

        hollow_left = left_marker["hollow"]
        before = left_marker if hollow_left else right_marker
        after = right_marker if hollow_left else left_marker
        bar_pixel = a[yc, (left_marker["x"] + right_marker["x"]) // 2]
        distances = [int(np.abs(bar_pixel - colour).sum()) for colour in series]
        rows.append(
            {
                "row": len(rows) + 1,
                "y": yc,
                "before": round(to_value(before["x"]), 3),
                "after": round(to_value(after["x"]), 3),
                "difference": round(to_value(before["x"]) - to_value(after["x"]), 3),
                "marker_radius": round((left_marker["radius"] + right_marker["radius"]) / 2, 2),
                "hollow_side": "left" if hollow_left else "right",
                "bar_rgb": [int(v) for v in bar_pixel],
                "series": f"series-{int(np.argmin(distances)) + 1}",
            }
        )

    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    for row in rows:
        for key, colour in (("before", (0, 130, 0)), ("after", (0, 0, 230))):
            x = first_x + (row[key] - ticks[0]) * px_per_tick
            y = row["y"]
            draw.line([(x - 7, y), (x + 7, y)], fill=colour, width=2)
            draw.line([(x, y - 7), (x, y + 7)], fill=colour, width=2)

    return {
        "ticks": ticks,
        "first_tick_x": round(first_x, 2),
        "pixels_per_tick": round(px_per_tick, 4),
        "background_rgb": [int(v) for v in bg],
        "gridline_rgb": [int(v) for v in grid],
        "plot_area": {"top": top, "bottom": bottom, "left": left, "right": right},
        "series_colours": [[int(v) for v in c] for c in series],
        "rows": rows,
        "overlay": overlay,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("image", type=Path)
    parser.add_argument("--ticks", required=True, help="comma-separated tick values, e.g. 5,6,7,8,9,10")
    parser.add_argument("--out", type=Path, help="JSON output path")
    parser.add_argument("--overlay", type=Path, help="diagnostic overlay image path")
    parser.add_argument("--tol", type=int, default=40, help="colour tolerance (default 40)")
    parser.add_argument(
        "--blend-tol",
        type=int,
        default=25,
        help="how close a pixel must be to the background-gridline blend to count as an "
        "antialiasing halo (default 25)",
    )
    args = parser.parse_args()

    ticks = [float(t) for t in args.ticks.split(",")]
    result = digitize(args.image, ticks, args.tol, args.blend_tol)
    overlay = result.pop("overlay")

    out = args.out or args.image.with_name(args.image.stem + "_values.json")
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    overlay_path = args.overlay or args.image.with_name(args.image.stem + "_detected.png")
    overlay.save(overlay_path)

    print(f"{len(result['rows'])} rows -> {out}")
    print(f"{'row':>4} {'before':>8} {'after':>8} {'diff':>8}   marker")
    for row in result["rows"]:
        print(
            f"{row['row']:>4} {row['before']:>8.3f} {row['after']:>8.3f} "
            f"{row['difference']:>8.3f}   hollow on {row['hollow_side']}, {row['series']}"
        )
    print(f"overlay -> {overlay_path}  (open it: the crosses must sit on the markers)")


if __name__ == "__main__":
    main()
