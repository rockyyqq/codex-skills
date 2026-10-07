---
name: photo-composite-editing
description: Edit a photograph non-destructively when a requested change (add/remove an object, replace a region, transplant an element from a reference photo) must leave everything else untouched. Covers capability checks before promising a result, keeping a known-good source file, exact-composite vs generative techniques, isolating a target region by connected-component labelling, matching a repaired region's tone to the surrounding skin, numerical boundary verification, and the Windows/PowerShell image-manipulation traps. Use for "add X to my photo", "remove Y", "put the tie/hat/background from photo B into photo A", "replace this dark patch with skin", "make this one higher resolution".
metadata:
  when_to_use: A user supplies one or more photos and wants a specific element added, removed or replaced while the rest of the frame stays identical. Also use when a previous attempt produced visible artefacts (strips, seams, patches, a dark band or grey wash) and you need to diagnose why. Also use when the user pastes an image and asks for a larger version, or asks you to clean up the working files at the end.
---

# Photo composite editing

Editing a photograph on request, without a generative image model, using pixel operations
and/or an external edit API. The hard part is almost never the element itself — it is
keeping the untouched 90% of the frame genuinely untouched, and knowing when to stop.

## 0. Scope the capability BEFORE promising anything

Run this first. It has saved entire sessions.

```
- Is an image-capable model available to this session? (check configured providers/credentials)
- Is there an image library? (python -c "import PIL"; node -e "require('sharp')")
- Can you install one? (pip/npm install reachable, or timed out?)
- Is git present if the plan needs a repo?
- Are there third-party image APIs callable with a key the user can supply?
```

Only then state what you can deliver. Promising a photorealistic edit and discovering
mid-way that the session is text-only wastes the user's time and your budget.

**Key realisation from practice:** a text-only session can still do this well, because
most editing APIs are plain HTTP. See §4.

## 1. Keep a known-good file (the irreversibility rule)

Never repair an image in place. Before the first edit:

- copy the source to `<work>/source.<ext>` and treat it as read-only
- every repair writes a **new** file (`v2`, `v3`, ...)
- if a repair fails verification, discard that file and restart from the known-good one

Multiple failed repairs compound: a fix for one artefact creates two more. Restarting
from source is almost always cheaper than patching the patched file.

## 2. Decide: generative or deterministical?

| Task | Method |
|---|---|
| Add an object that must look photographic (a tie, a hat, a person, a background) | Generative — external edit API (§4) |
| Move/copy an existing region between two images of the same subject | Exact composite (§3) |
| Remove a thin defect, line, or small blemish on a smooth surface | Deterministic fill (§3) |
| Anything requiring invented 3-D form, fabric drape, or new lighting | Generative. Do not attempt procedurally |

**Do not hand-render photographic content.** Vector shapes, procedural texture and
gradients read as illustration, never as a photograph, and the user will see it instantly.
If no generative path exists, say so and offer alternatives (§6).

## 3. Deterministic technique

### 3a. Measure the boundary numerically, never by eye

Before writing any fill, measure the actual pixel structure. Scan rows/columns and print
class maps and runs — do not reason from a downsampled preview.

```powershell
# per-row dark runs inside a region: what is where, and how wide
foreach($y in $rows){
  $runs=@(); [int]$rs=-1
  for($x=$X0;$x -le $X1;$x++){
    $o=$y*$st+$x*3
    $lum=0.299*$buf[$o+2]+0.587*$buf[$o+1]+0.114*$buf[$o]
    if($lum -lt $THRESH){ if($rs -lt 0){$rs=$x} }
    else { if($rs -ge 0){ if(($x-$rs) -ge 5){ $runs+="$rs-$($x-1)" }; $rs=-1 } }
  }
  "y=$y  " + ($runs -join "  ")
}
```

Also print a **class map** (skin / white / dark / other) as characters — one glance shows
structure that numbers hide. Then confirm with a zoomed crop of the source.

When more than one dark thing is in the region (an artefact **and** a garment), go one step
further and label connected components, colour-code them, and print their statistics. This
single diagnostic resolved a problem that three threshold passes had failed to, and it is
the fastest way to answer "which dark thing is which":

```
1. candidate mask = single luminance threshold over the region
2. label 8-connected components
3. render one palette colour per component OVER the photo, and emit a crop of it
4. print per component: id, size, bbox, mean RGB, mean R-B
```

```
id  size   x0..x1      y0..y1      meanRGB      R-B   keep
1   62493  611..1218   1500..1909  133,103,85   -48   <- the artefact
8   50728  1210..1399   1609..2049   39,42,58    19   <- jacket
9   27778   480..579    1616..2049   50,60,91    41   <- jacket
42  23393   745..1043   1933..2049   44,53,82    38   <- tie
```

Print the table **and** look at the overlay. The table gives you the hue separation to drop
garments automatically; the overlay is what catches the component you did not expect.

### 3b. Identify the target by connectivity, not by threshold

A threshold finds *every* pixel of that brightness — including the dark clothing right next
to it. Real numbers from a neck repair: the navy jacket shoulder sampled `rgb(25,23,30)`
(`B-R = +5`) and the dark band to be removed sampled `rgb(26,25,24)` (`B-R = -2`). One
threshold pass over that pair filled 101,475 px and ate both shoulders.

No threshold and no **per-pixel** hue test can separate those. **Connectivity can**, because
the collar physically separates the artefact from the jacket. So: threshold once, label the
components, then decide per component.

Two rules that follow from that:

- **Judge hue on the component mean, never per pixel.** Parts of the artefact were genuinely
  neutral (`R-B` ≈ -12) while the jacket means sat at -18…-40. A per-pixel warm test silently
  drops the neutral parts and leaves a grey ghost of the original shape behind — visible only
  when you zoom.
- **Keep only components above a minimum size (~300 px).** Beard stubble, sensor noise and
  fabric grain break into hundreds of tiny components. Filtering by size is what makes "keep
  everything else unchanged" true rather than aspirational.

Also bound the region so the mask cannot reach a collar/jacket gap. A neutral-grey strip
there is *not* neck, and a component-mean rule will happily accept it — check the overlay at
that boundary before trusting the mask.

### 3c. Prefer exact composite over threshold fill

A threshold-based fill ("replace pixels darker than X") fails whenever the boundary is a
*gradient* rather than a step — which is typical at a jaw/neck junction, a collar edge, or
a shadow under a chin. It will either miss part of the target or eat legitimate shading,
and then it bleeds into neighbouring surfaces.

**Use instead:** take a clean region from a source image and composite it with an explicit
rectangle plus a feathered alpha. No detection means nothing can spill.

```powershell
# feathered rectangle composite: dst <- src over a bounded box
for($row=$RY0;$row -le $RY1;$row++){
  $aT=[Math]::Min(1.0,($row-$RY0)/[double]$FEATHER)
  $aB=[Math]::Min(1.0,($RY1-$row)/[double]$FEATHER)
  $a=$aT*$aB
  for($x=$RX0;$x -le $RX1;$x++){
    $eL=[Math]::Min(1.0,($x-$RX0)/[double]$FEATHER)
    $eR=[Math]::Min(1.0,($RX1-$x)/[double]$FEATHER)
    $aa=$a*$eL*$eR
    $o=$row*$dstStride+$x*3; $p=$row+$srcStride+$x*3   # (mind the multiply)
    $buf[$o+2]=[byte][Math]::Round($buf[$o+2]*(1-$aa)+$src[$p+2]*$aa)
    # ... +1, +0 likewise
  }
}
```

**Boundary placement is the whole game.** Put the composite edge where the two sources
are most similar (inside a shadow, along a fabric edge, in flat skin) — not in the middle
of a gradient.

### 3d. Filling a region: sample clear of the defect, and grade

When you must fill rather than composite:

- sample the replacement colour **well clear** of the defect (for a neck shadow, 25–40 px
  above it, not adjacent) — adjacent pixels are already darkened and the fill will read
  as a flat plate
- apply a **vertical gradient** across the filled band so the natural shading ramp is
  preserved; a flat fill on a curved surface is instantly visible
- feather both seams by a few px
- low-pass the sampled colour **horizontally** (±20–25 px) so neighbouring columns agree;
  otherwise per-column sampling produces vertical streaks

### 3e. Lifting a shadow or dark band so it matches surrounding skin

The hardest case in practice, and the one most likely to come back to you as "now it looks
like a smear". Four decisions decide whether it reads as repaired skin or as a patch.

**1. Take the region's own tone with a mask-normalised blur, not a plain blur.**
`blur(image)` inside the band averages in the bright skin around it, so your "before" tone is
already half-corrected and you apply far too little lift. Measured: only 16–21 levels when
~70 was needed. Use `blur(x·m) / blur(m)` where `m` is the mask, so the low-frequency tone is
the region's *own*.

**2. Interpolate between the skin above AND the skin below the band.** Two-sided
interpolation follows the neck's real gradient, and it makes any halo a near no-op wherever
the pixels are already skin — which is what lets you be generous with the halo.

**3. Choose source pixels on both a colour test and a distance test.** Sampling "skin" at
`lum ≥ 165` picks up the darkened annulus hugging the mask, which drags the target tone down
and under-corrects (19–25 levels instead of ~50). Sample only clear skin (~`lum ≥ 198`,
saturated warm) **and** restrict it to a band within ~40 px of the mask, so the target is the
*local* surrounding tone rather than the brightest skin in the frame. The two mistakes pull
in opposite directions — under-sourcing gives a grey result, over-sourcing gives a pale one.

**4. Impose the target's hue; keep the region's own luminance texture.** Do **not** add a
constant offset `(target - current)` per channel. On a pixel that already carries a blue
cast, adding to all three channels raises B faster than R and makes it *more* blue — that is
exactly the pale grey wash that looks worse than the band it replaced. Instead take the
target's chromaticity and the region's own shading:

```
L_target = luminance of the sampled skin
L_low    = low-frequency luminance of the region (mask-normalised)
L_out    = L_target + (L_current - L_low)     # keeps texture and gradient
out_c    = target_c * (L_out / L_target)      # adopts skin's hue exactly
```

**Halo size must come from the measurement, not from taste.** A soft ramp at a jaw/neck
junction ran 34 → 204 in luminance over ~55 px. A 12 px dilation left a visible ghost outline
of the original band; 18 px over-ran into genuinely shadowed neck and left white streaks.
Measure the ramp width first (§3a), then size the halo, and prefer a criterion anchored to
local skin luminance over a fixed pixel distance.

**Never hard-cut at the analysis boundary.** Cutting the fill at your region edge leaves a
clean vertical seam, obvious the moment the user zooms. Prefer extending the mask to a
*natural* boundary (the collar edge, a fabric line). If the artefact runs off the region you
can analyse, fade the boundary instead — but know that a *partial* alpha on a hue-changing
fill tints the fringe (we got an orange smear sitting above a grey band). And confirm that
any feather you believe you applied is actually wired up: an unused `-AlphaBlur` parameter is
a silent no-op, and a visibly jagged mask edge survived three iterations before anyone
noticed the parameter was never called.

Finally, sanity-check magnitude: print the mean shift you applied in levels and compare it
against the defect depth you measured. Over-correcting is as visible as under-correcting — we
produced both directions, and each looked worse than the band it replaced.

### 3f. Verify objectively after every pass

After each edit, re-run the measurement from §3a on the **output** and compare against the
source. Also produce an A/B crop at 2× at the exact edit site. If a band of pixels changed
that you did not intend to change, discard and restart (§1).

The strongest cheap acceptance test is a **whole-image invariant**:

```
declared region:       x 480..1400, y 1470..2060
changed OUTSIDE region: 0
changed INSIDE region:  85,240 px
```

Count differing pixels between source and output across the *entire* image, not just around
the edit, and report the number. Zero outside the declared region is a fact the user can
check; "looks good" is not. Naming the pixel count you did change finishes the conversation
instead of starting a new one.

## 4. Generative technique via HTTP (Hugging Face / Gitee)

Most "AI image editor" front-ends are thin clients over plain HTTP endpoints. You can call
them directly — no browser automation needed.

**Hugging Face Gradio Spaces** (e.g. a Qwen-Image-Edit space). Auth header is optional; a
ZeroGPU space refuses **anonymous** GPU work, so a token is effectively required.

```
1. POST {base}/gradio_api/upload            multipart field "files"  -> ["/tmp/gradio/<hash>/name.jpg"]
2. POST {base}/gradio_api/queue/join        JSON {data:[...], fn_index, trigger_id, session_hash, event_data:null}
3. GET  {base}/gradio_api/queue/data?session_hash=...   Accept: text/event-stream
   -> read SSE lines; msg "process_completed" with success:true -> output.data[0][0].image.url
4. download that URL
```

Read the space's own contract before guessing: `GET /config` gives `dependencies` (find
your `api_name`) and `components` (input order, labels, defaults). A typical edit payload is
`[imagesGallery, prompt, seed, randomizeSeed, guidanceScale, steps, height, width, rewritePrompt]`.

**Gitee AI** (OpenAI-compatible, free daily quota): `POST https://ai.gitee.com/v1/images/edits`
as multipart with `prompt`, `model=Qwen-Image-Edit`, `num_inference_steps`, `cfg_scale`,
`response_format=url`, and one or more `image` fields. A `mask` field is **not** supported —
adding it returns a 500. Returns a URL.

### Prompting rules that matter

- **Attach the reference image.** Without it the model invents a generic version of the
  requested element. With it you get the actual pattern/colour.
- **State preservations explicitly and last**: "keep the face, hair, jacket and background
  exactly as they are; do not crop, zoom or reframe".
- **Watch the returned size.** Models frequently ignore requested dimensions. If the output
  aspect ratio differs from the source, the model *reframed* — that is a rejection, not a
  resize. Requesting a portrait aspect ratio usually restores full framing.
- **Expect invented changes.** A model asked to fix the neck may also add stubble, darken a
  jaw, or alter a collar. Diff the result against the source and composite around the
  unwanted edits (§3b) rather than accepting them.

## 5. Windows / PowerShell image traps

These cost real time. They are specific and repeatable.

| Trap | Symptom | Fix |
|---|---|---|
| Hashtable keys `W`, `H`, `Count`, `Keys` | `$h.W` returns null/0 | use `imgW`, `imgH` — never collide with automatic properties |
| Assignment inside a function | function returns an array of stray values | suppress with `[void]` / `$null =`, or only `return` one thing |
| Variable names are case-insensitive | `$by` (array) clobbered by `for($by=...)`; `$bt` aliases `$BT`; `$KH` affected by `$kh` | prefix locals meaningfully: `$row`, `$bandTop`, `$knotH` |
| Expressions inside `@(...)` | `@($x-1)` parsed as a command → "op_Subtraction" error | parenthesise: `@($x-1)` → `@(($x-1))` |
| Function call after an operator | `255*Sm(...)` fails to parse | assign first: `$s=Sm(...); 255*$s` |
| String concat with `+` in a loop | silently produced empty strings | build a `List[string]` and `-join` it |
| `WriteAllLines` default encoding | file read back as "binary" | pass `(New-Object System.Text.UTF8Encoding($false))` |
| `LockBits(..., ReadOnly, ...)` then writing the buffer | `UnlockBits: generic GDI+ error` | lock `ReadWrite` if you modify the buffer |
| Reading `.Stride`/`.Width` after `Dispose()` | 0×0 canvas, or `New-Object Bitmap` "Parameter is not valid" | capture `imgW`/`imgH`/`stride` into locals **before** disposing |
| Indexing past buffer end in a blur | GDI+ UnlockBits error, or silent corruption | clamp rows/cols to `1..H-2`, `1..W-2` before neighbour reads |
| `Invoke-WebRequest` to a modern TLS host | "underlying connection was closed" | use `node` (modern TLS) instead of Windows PowerShell for HTTP |
| Naive box blur, `O(n·r)` | a 400×600 region takes **minutes** in PowerShell | use a separable prefix-sum blur — window sum = `P[x+r+1] - P[x-r]` — which is `O(n)` regardless of radius |
| Per-pixel loop over a 4M-pixel image | script looks hung | work on the region only; for very large fills, downsample ~4×, propagate there, then bilinear-upsample |
| A parameter declared but never used | silent no-op; the defect survives and you blame the method | grep your own script for the parameter name before concluding the technique failed |
| Blur/index loops reading `1..N` without clamping | GDI+ error or silent edge corruption | clamp neighbour reads to `1..H-2` / `1..W-2` |

**Safest save pattern** — write into the buffer you already locked:

```powershell
LockBits(..., ReadWrite, Format24bppRgb) -> copy to byte[] -> mutate -> copy back -> UnlockBits -> Save
```

Do not build a second bitmap from dimensions to save; that is where the "Parameter is not
valid" errors come from.

## 6. Reporting discipline

- **Say what changed, in numbers.** "264,889 px restored from your original jaw" beats
  "I fixed the jaw".
- **Flag residual defects yourself** before the user finds them — a faint seam, a slight
  asymmetry. Name the parameter that would fix it.
- **Do not iterate silently.** After two failed attempts at the same artefact, stop and
  change method or hand it back. Patching a patched file degrades the result and burns
  trust; state the limitation plainly and offer the alternatives.
- **Offer the human-in-the-loop path** when a brush beats a threshold: a local editor the
  user can drive, with the exact coordinate ranges and prompt to use. Beats another failed
  automated pass.

## 7. Redirecting to the right tool

When the geometry between two photos genuinely differs (different pose, scale or framing)
a paste cannot work and a procedural render will look fake. The honest answer is a
generative inpainting tool. Give the user:

- the exact mask region, as absolute pixels **and** as percentages of width/height
- a mask PNG (white = repaint, black = keep) plus an overlay preview showing coverage
- the prompt, and the instruction to attach the reference image
- an acceptance checklist (nothing outside the mask changed; edge sits correctly; pattern
  scale matches; no hard horizontal cut)

That package is a real deliverable, not a cop-out — it is often what finishes the job.

## 8. Matching a pasted image to a file, and delivering a larger version

When the user pastes an image and says "this one is good", you usually do not know which file
it is — by then the folder may hold dozens of near-identical candidates. Identify it instead
of guessing: signature every candidate and rank by difference.

- downsample each image to a small grid (48×48) and average-compare channel-wise, ranked by
  mean absolute difference
- `0.00` means byte-identical. A small residual between a JPEG and a PNG of the same picture
  (mean ~0.2/255, max ~8) is **JPEG noise**, not a different edit — that is the signature of
  a lossless twin

That second case is the valuable one: it finds a **lossless master** of the image the user
chose. Upscale from the PNG, not the JPEG, or you compound compression artefacts into the
enlarged file.

For "get me a high-resolution version":

- `InterpolationMode.HighQualityBicubic` + `PixelOffsetMode.HighQuality` + `WrapMode.TileFlipXY`
  via `ImageAttributes` — the wrap mode is what prevents edge ringing
- save both a lossless PNG and a quality-95 JPEG; the PNG costs ~9× the size and is worth it
- inspect the output at **1:1** in an edge-rich area (eyes, hair), not zoomed out, to check
  for halos
- **say plainly that this is resampling, not new detail.** Doubling the pixel dimensions
  satisfies a print or upload requirement; it cannot invent detail that was never in the
  original. If the user needs genuinely more detail, that is an AI upscaler or a re-render —
  name which of those is actually available rather than leaving the impression you added some.

## 9. Handback: separating finals from work, and cleaning up

By the end of a job like this the folder holds hundreds of intermediates — and the version
the user just approved is sitting in that same folder. "Remove the work files" is therefore
both destructive and ambiguous; treat it that way.

- **Enumerate first**, grouped by folder, and state plainly which files are the originals and
  which are the approved final. Originals are irreplaceable; say so out loud.
- **Never delete without a verified keep-list.** Check every keep-file exists *before* removing
  anything, and abort the whole operation if one is missing.
- **Confirm each recursive target resolves inside the intended root** before deleting; compare
  the resolved path against the root prefix and refuse anything else.
- **Prefer the Recycle Bin** — `Microsoft.VisualBasic.FileIO.FileSystem.DeleteDirectory(...,
  RecycleOption.SendToRecycleBin)` — over a hard delete, and tell the user how to recover. If
  the folder is cloud-synced, note that the deletion syncs too and the provider keeps its own
  copy for a limited window.
- **Never overwrite a filename you did not create.** Other agents may be working the same
  folder in parallel; we watched five new files appear mid-session. Version your outputs.
- Report counts and sizes removed, what was kept, and anything you deliberately left alone
  because it fell outside the stated scope.
