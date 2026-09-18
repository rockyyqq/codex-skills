#Requires -Version 7
<#
  The periodic review. Reads the vault, computes what is due, writes the report
  to a file, and prints counts and the path only.

  It prints no record content: stdout is persisted by the session store, so a
  role label or a medication name on stdout would defeat the whole design.
#>
[CmdletBinding()]
param(
    [string]$OutDir,
    [string]$Today
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'vault.ps1')
. (Join-Path $PSScriptRoot 'record_gaps.ps1')

Assert-Boundary

$ledgerPath = Join-Path $PSScriptRoot '..\references\sources.json'
$todayDate  = if ($Today) { [datetime]::ParseExact($Today, 'yyyy-MM-dd', $null) } else { Get-Date }
if (-not $OutDir) { $OutDir = Join-Path $script:VaultRoot 'reports' }

# A source past its review date means nothing dependent on it can be judged.
$stale = @()
if (Test-Path -LiteralPath $ledgerPath) {
    $ledger = Get-Content -LiteralPath $ledgerPath -Raw | ConvertFrom-Json -AsHashtable
    foreach ($source in $ledger['sources']) {
        if ($source['review_by']) {
            $review = [datetime]::ParseExact($source['review_by'], 'yyyy-MM-dd', $null)
            if ($review -lt $todayDate) { $stale += $source['id'] }
        }
    }
} else {
    $stale += 'ledger-missing'
}

$facts = @(); $assumptions = @(); $unknown = @(); $people = 0
$record = Get-VaultRecord
if ($record -and $record['people']) {
    $people = $record['people'].Keys.Count
    foreach ($personKey in $record['people'].Keys) {
        $person = $record['people'][$personKey]

        # Completeness, from the one shared definition. An unrecorded or unknown
        # field is not a pass: the review must not report a clean count on
        # something it never assessed.
        foreach ($gap in (Get-RecordGaps -Person $person)) {
            $unknown += "- $personKey / $gap"
        }

        # A booked procedure with an outstanding pre-operative step is a due
        # item. Reporting OK while it is outstanding is the false-reassurance
        # failure this script exists to avoid.
        foreach ($procedure in @($person['planned_procedures'])) {
            if (-not $procedure) { continue }
            if ($procedure['status'] -eq 'booked' -and $procedure['pre_op_outstanding']) {
                $planned = $procedure['planned_for']
                $facts += "- $personKey / $($procedure['code']): pre-operative step outstanding, planned $planned"
            }
        }

        foreach ($event in @($person['events'])) {
            # A null section yields @($null), which is one null element, not zero.
            if (-not $event) { continue }
            if (-not $event['last_done'] -or -not $event['interval_months']) { continue }
            $last  = [datetime]::ParseExact($event['last_done'], 'yyyy-MM-dd', $null)
            $dueOn = $last.AddMonths([int]$event['interval_months'])
            if ($dueOn -lt $todayDate) {
                $line = "- $personKey / $($event['code']): due $($dueOn.ToString('yyyy-MM-dd'))"
                if ($event['basis'] -eq 'assumption') { $assumptions += $line } else { $facts += $line }
            }
        }
    }
}

$cannotJudge = @()
foreach ($source in $stale) { $cannotJudge += "- source past its review date: $source" }
$cannotJudge += $unknown

if ($stale.Count -gt 0 -or $unknown.Count -gt 0) { $status = 'CANNOT JUDGE' }
elseif ($facts.Count -gt 0) { $status = 'DUE' }
else { $status = 'OK' }

$stamp = $todayDate.ToString('yyyy-MM-dd')
$lines = @(
    "<!-- kind: review -->",
    "# Household review — $stamp",
    "",
    "**Status: $status**",
    "",
    "## Facts",
    "",
    # -join, not the bare array: a multi-element array stringifies to
    # 'System.Object[]' when the outer -join touches it. One element unwraps to a
    # scalar and looks fine, so this only breaks once there are two items.
    $(if ($facts.Count) { $facts -join "`n" } else { "- nothing due" }),
    "",
    "## Assumption-dependent — questions for a clinician",
    "",
    $(if ($assumptions.Count) { $assumptions -join "`n" } else { "- nothing to raise" }),
    "",
    "## Cannot judge",
    "",
    $(if ($cannotJudge.Count) { $cannotJudge -join "`n" } else { "- nothing outstanding" }),
    "",
    "## What this is not",
    "",
    "Date-based items were checked against dated sources. Conditions were **not**",
    "assessed, nothing was examined, and no conclusion about a person was drawn.",
    "These checks being up to date does not mean anyone is healthy.",
    ""
)

if (-not (Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }
$reportPath = Join-Path $OutDir "$stamp-review.md"
Set-Content -LiteralPath $reportPath -Value ($lines -join "`n") -Encoding utf8

# Counts and the path only. Never the content.
Write-Output "status: $status"
Write-Output "people: $people"
Write-Output "due (facts): $($facts.Count)"
Write-Output "to raise: $($assumptions.Count)"
Write-Output "cannot judge: $($cannotJudge.Count)"
Write-Output "report: $reportPath"
