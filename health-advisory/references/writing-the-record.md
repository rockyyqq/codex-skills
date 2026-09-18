# Writing to the record

The vault is written by scripts, and four traps have each cost a real defect in
this skill. They are collected here because every one of them fails **quietly** —
which is the property the whole design exists to remove.

## `Add-Member` on a hashtable does not survive serialisation

It attaches a PowerShell property that `ConvertTo-Json` ignores. The value is
written, the script reports success, and the key is simply not there.

```powershell
$entry['note'] = '...'                    # persists
$entry | Add-Member -NotePropertyName note -NotePropertyValue '...'   # silently lost
```

Set keys by indexing. After a write, check that the key exists rather than
trusting that the write succeeded.

## `@($null).Count` is 1, not 0

Wrapping a null section in `@()` produces an array containing **one null**, so a
missing section counts as one item — and a `foreach` body runs once on `$null` and
throws. Guard every element:

```powershell
foreach ($item in @($person['section'])) { if (-not $item) { continue } }
```

## A multi-element array inside a string becomes `System.Object[]`

A single-element array unwraps to a scalar and looks fine, so this hides until a
record has two items. Join explicitly rather than relying on the outer `-join`:

```powershell
$(if ($items.Count) { $items -join "`n" } else { '- none' })
```

## `Write-Error` throws before `exit N` runs

Under `$ErrorActionPreference = 'Stop'`, a CLI error path that must return a
specific exit code never reaches it. Use:

```powershell
[Console]::Error.WriteLine("message"); exit 2
```

## Dates are ISO everywhere

A date written as "7 July 2026" matches the identifier check's date-of-birth
pattern. That is not a false positive to loosen — it is a convention to keep, so
the check stays strict enough to catch a real date of birth.
