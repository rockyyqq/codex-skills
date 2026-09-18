# Reading artifacts back, and looking at renders

A build that exits 0 and a human-looking screenshot are claims, not evidence. Two habits turn them
into evidence: open what was actually built, and look at what was actually drawn.

## Read the built artifact back

After packaging, open the artifact with a reader and assert the things you just claimed:

- the payload really came from this tree, file by file (compare bytes);
- the name/label/identity you set is the one inside, and no older one is left;
- the resources the platform will resolve exist, and point where you think;
- nothing you promised not to touch was touched.

Two specific lessons that generalise:

- **A packaging step's success is not the artifact's state.** Have a separate read-back check that
  can fail on its own; when it fails against an older build, that is the check working.
- **Never overwrite the last good artifact.** Keep the previous ones under names that say what changed,
  and say which one a user is currently running.

## Patching something built, in place

When you may not rebuild -- a signed package, a vendor binary, a compiled resource table -- you may still
re-point parts you own, if you respect the container:

- **Equal-length swaps only**, in string pools or fixed-width fields, so nothing after them shifts.
  Assert the two lengths are equal rather than trusting your eye.
- **Swap only what you own**: an asset path, a label, an identifier. Never the compiled logic.
- **Give the platform the form it expects.** A slot documented as an adaptive icon wants a real
  adaptive icon; dropping a bitmap there left it with no density, and the launcher drew a *corner* of
  the artwork -- reproducibly, at two different pixel sizes, which is what identified the cause.
- **Say what you deliberately did not do.** "The layers are flattened because adding a drawable means
  rebuilding the resource table" is a decision; leaving it unsaid is a trap for the next person.
- **Guard the key**: a signing key that is lost means no future build can install over the last one.
  Keep it out of version control and say so where the build is documented.

## Look at what you drew

Render every screen you changed, then open the image and examine it. Findings that no check produced
have come from exactly this:

- a launcher icon cropped to one corner by a device mask;
- a grey bar and a shadow along the bottom of every screen, because an empty container still paints
  and a closed panel still casts;
- buttons 100px wide inside a 416px parent, their labels touching both edges.

How to look properly:

- **Crop and zoom the edges.** Neither the shadow nor the cropped icon was visible in a full-screen
  view at 1x; both were obvious at 2x on the bottom 130px or in a corner.
- **Simulate the device.** Mask the drawing the way the platform will, at the size it will, and check
  the result still reads. A design can be correct and still lose its meaning in a circle.
- **Check the smallest size** the artwork will be seen at, not the largest.
- **A blank or wrong image is usually a harness problem, not a design problem.** Confirm the page
  actually loaded -- a screenshot of an error page looks like a screenshot of a white design.
- **Mind the clock.** Headless capture with accelerated virtual time runs timers: a toast that hides
  itself after five seconds is gone if the budget is eight. Budget shorter than the transient, or
  capture the state deliberately.

After looking, change what is wrong *before* writing checks around it: the checks then pin the fixed
behaviour, and the drawing stays the source of truth.
