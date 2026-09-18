# The local loop on Windows

How to run, test, screenshot and package a local app from a shell in this environment, and the traps
that have each cost an hour at least once. Everything here is about *this* environment; the loop
itself is language-agnostic.

## Seeing the app without building it

A local single-page app needs no server and no package: open it in a browser with an argument that
puts it into a safe sample mode.

```powershell
# with a saved profile of "looks", each opening one screen of the sample
.\preview.ps1 -List
.\preview.ps1 -Look <name>
```

Keep the sample mode strictly in memory -- a page opened to *look* must never write its sample over a
real user's stored data -- and say so where the sample is built.

## Running headless Chrome to check a page

```powershell
& $chrome --headless=new --no-sandbox --in-process-gpu --disable-gpu `
  --disable-software-rasterizer --no-first-run --allow-file-access-from-files `
  --hide-scrollbars --user-data-dir="$env:TEMP\run-1" `
  --window-size=560,1000 --virtual-time-budget=6000 `
  --screenshot="C:\abs\path\shot.png" 'file:///C:/abs/path/index.html?arg=1'
```

- `--allow-file-access-from-files` -- without it a page cannot reach into another `file://` document,
  which is how a test harness inspects the app in an iframe.
- `--in-process-gpu`, `--disable-gpu`, `--disable-software-rasterizer` -- without these the GPU process
  dies here and the browser exits before rendering anything.
- `--user-data-dir` in the temp folder -- a throwaway profile, so a run cannot inherit or leave state.
- `--dump-dom` -- for reading a verdict out of the page; combine with the same flags.
- `--virtual-time-budget=<ms>` -- how far the page's clock is allowed to run. Too short and the page
  has not painted; too long and every timer has already fired.
- `--window-size=<w>,<h>` -- a viewport, not a phone. Capture wider than the design's own width or the
  right edge is cut, and make it taller than the page when you need to *see* something below the fold.

## Traps

| trap | what happens | do instead |
|---|---|---|
`"$app?demo=1"` in PowerShell | `$app?demo` is read as one variable name and the URL becomes rubbish -- the "screenshot" is the browser's error page | build the URL by concatenation, or put the whole URL in single quotes |
`2>$null` on a browser call | Chrome's own output (including "wrote file ...") is discarded, and a failed capture looks silent | let stderr through, or capture it to a file and read it |
node run from a sandboxed shell | `EPERM: lstat 'C:\Users\<you>'` instead of your script running | `node --preserve-symlinks --preserve-symlinks-main <script>` |
`Set-Content -NoNewline` with an array | the lines are joined with no separator, silently corrupting the file | write arrays with a normal redirect, or set the text explicitly |
a PowerShell heredoc | there isn't one | write the text to a file with an editing tool, and pass the file's path to the command |
`$i:` inside a string | parsed as a drive-qualified variable | `${i}:` |
git in a folder owned by another user | "dubious ownership" refusal | `git -c safe.directory='*' -C <repo> ...` |
git commit with a long message | quoting eats the body | write the message to a file, then `git commit -F <file>` |

## Running long suites without guessing

- A suite that pipes through a filter buffers everything until it finishes: you learn nothing while it
  runs. Either read the raw output, or accept that no news is expected.
- To tell whether a long run is progressing, look at what it spawns:
  `Get-Process python,node,chrome | Select-Object ProcessName,Id,StartTime` -- a fresh start time each
  time you look means it is cycling.
- Prefer a filter flag that runs one area of the checks (`--area`, `--only`) while iterating, and run
  the whole sweep once at the end.

## A read-only project folder

When the working project cannot be written to, author in a copy you *can* write to and copy finished
files across with an approval. Keep three things straight: which copy is authoritative, which files
were actually copied, and whether the copy is in step with the last commit. Verify a copy by running
the suites against the destination afterwards -- not by assuming.
