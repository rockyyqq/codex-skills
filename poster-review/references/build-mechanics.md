# Build mechanics

These have each caused a real defect on a delivered poster. Check them rather than rediscovering them.

## PowerPoint construction

- **Text boxes carry no side insets.** PowerPoint's default inset is 0.1 in (about 10 px) on each side.
  Leaving it in place narrows every column by roughly 19 px and pushes whole paragraphs onto extra lines,
  so a build that fits in the HTML source overflows in the deck. Set `insets` to zero on every text box and
  treat the box geometry as the typographic geometry, exactly as the print build does.
- **A line-spacing percentage is applied to a line box, not to the font size.** The font's line box is about
  1.2 x the em, so a spacing of 1.42 produces a pitch of `size * 4/3 * 1.42 * 1.2` px, not
  `size * 4/3 * 1.42`. Ignoring that extra 1.2 under-sizes every text box by 20 percent, and the overflow is
  invisible in the source file because it only appears when the deck is rendered. This is what pushed the
  Discussion over the citation line and off the foot of page 1.
- **Estimate the wrap with the right average glyph width.** For Segoe UI at poster sizes, mixed prose runs at
  about 0.465 em per character against the full box width. Using 0.45 em over-estimates characters per line,
  under-estimates the number of lines, and yields a box that is too short. Calibrate against a render before
  trusting any estimate: put the paragraph in a generously tall box, render, and count the line bands.
- **Font size is in pixels, not points.** The presentation API's `fontSize` value is multiplied by 0.75
  when written to the file, so a value of 8 becomes 6 pt. Divide the intended point size by 0.75 before
  setting it, then confirm by reading the `sz` attribute out of `ppt/slides/slideN.xml` where the value is
  in hundredths of a point. Getting this wrong made a whole deck render 25 percent small and look sparse.
- **Never position a text box with an expression that can go negative.** A panel subtitle computed as
  `x + width - 230` landed at x = -47 px and was drawn on top of its own heading, which the user saw as
  text mixed together. Stack headings and subtitles vertically instead of placing them side by side in a
  narrow panel.
- Keep headings and subheadings in one consistent style across all sections of a slide.
- **Reserve the foot of the page before laying out the last block.** Put the citation and ethics footer at a
  fixed y, then size the final paragraph against the space remaining above it. Working top-down and hoping
  the footer still fits is how the last line of the Discussion ended up past the bottom of the page, where
  nobody would see it.

## Layout checks before delivery

- Overlap and boundary check with the geometry inspector:
  `container_tools/inspect_presentation_layout_geometry.py <file.pptx>` from the presentations skill.
  It reports text-frame overlaps and objects outside the slide. Aim for zero of both.
- **The geometry inspector does not see text overflowing its own box.** It compares frame rectangles, so a
  paragraph spilling out of a too-short box passes clean. Render the deck and measure ink as well: with
  Python and PIL, scan the exported PNG row by row, group rows that carry dark pixels into bands (one text
  line is a band about as tall as the line pitch), then check that no band crosses into the next block, that
  no band is far denser than its neighbours - the signature of two texts drawn on top of each other - and
  that the lowest band sits clear of the page foot.
- A panel drawn after a text block hides that block's overflow instead of revealing it. The Programme panel
  sat over the last third of the Background paragraph, so the render looked clean while the text was in fact
  running underneath it. Compare each paragraph's rendered line count against its own box, not just against
  the page.
- Blank-space check by rendering the page and measuring ink coverage per band. Report the largest wholly
  blank band; a normal section gap is fine, a quarter of the page is not.
- Re-render after every change to type size, and re-measure. Type size changes move everything below them.

## PDF export

- Chrome's headless print honours the CSS `@page` size. To produce a large-format poster from artwork laid
  out at a smaller size, set the larger `@page` **and** apply an explicit scale transform to the body;
  setting only the page size leaves the artwork at its original physical size in the corner of the sheet.
  For A4 to A0 the factor is exactly 4.
- Confirm the page box in millimetres and the number of pages after export. A poster that spills to a
  second page is a failed export, not a style problem.
- Check that fonts embed as Type0 rather than Type3, and that text stays vector. Confirm no raster images
  were introduced.

## Compliance items that are easy to miss

- Print the assigned finalist or abstract identifier where the event requires it, in the required corner.
- Match the exact page sizes and orientation the event specifies, and state them back in millimetres.
- Confirm which single file is the submission copy, and label it as such so the wrong version cannot be
  sent by mistake.
