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

# Words that carry no substance. A placeholder entry such as "no known drug
# allergies" must not be matched against anything, so it reduces to no words and
# the cross-check skips it.
$script:ClinicalStopWords = @(
    'known','none','no','not','nil','drug','drugs','allergy','allergies','allergic',
    'reaction','recorded','unspecified','unknown','applicable','tested','other',
    'than','which','when','less','more','with','from','into','that','this','the','and'
)

function Get-ClinicalWords {
    param([string]$Text)
    # A List, not an array. A bare `return @(...)` collapses one match to a
    # scalar and no matches to $null, and $null.Count throws under StrictMode;
    # wrapping the caller in @() then double-wraps whatever the comma preserved.
    # A List is one object, so .Count and .Contains are unambiguous either way.
    $words = [System.Collections.Generic.List[string]]::new()
    if (-not $Text) { return $words }
    $clean = ($Text.ToLower() -replace '[^a-z0-9\u4e00-\u9fff]+', ' ')
    foreach ($word in ($clean -split '\s+')) {
        if ($word.Length -lt 4) { continue }
        if ($script:ClinicalStopWords -contains $word) { continue }
        if (-not $words.Contains($word)) { $words.Add($word) }
    }
    # The leading comma is load-bearing. Returning the List bare lets the pipeline
    # unroll it: one element becomes a scalar, none becomes $null, and $null.Count
    # throws under StrictMode. This is the third shape of the same trap in this
    # file, after the array-return and the @()-around-a-comma cases.
    return ,$words
}

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
$nextDue = $null
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

        # A recorded allergy and a recorded medication sharing a word is a fact, not
        # a judgement. It is deliberately a word match on what is written down: it
        # is not an interaction check - that is a label question - and finding no
        # match clears nothing.
        foreach ($allergy in @($person['allergies'])) {
            if (-not $allergy) { continue }
            $allergyWords = Get-ClinicalWords -Text $allergy['substance']
            if (-not $allergyWords.Count) { continue }
            foreach ($medication in @($person['medications'])) {
                if (-not $medication) { continue }
                $medicationWords = Get-ClinicalWords -Text $medication['name']
                if (-not $medicationWords.Count) { continue }
                $shared = @($allergyWords | Where-Object { $medicationWords.Contains($_) })
                if ($shared.Count) {
                    $facts += "- $personKey / a recorded allergy and a recorded medication share the word '$($shared[0])': '$($allergy['substance'])' against '$($medication['name'])'"
                }
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
            # The next review date is computed from the earliest sourced interval,
            # not fixed to a calendar month. An interval nobody has sourced cannot
            # produce a date, which is why that case is reported as a gap.
            elseif ($null -eq $nextDue -or $dueOn -lt $nextDue) { $nextDue = $dueOn }
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
    "## Next review",
    "",
    $(if ($nextDue) { "Earliest item coming due: **$($nextDue.ToString('yyyy-MM-dd'))**" } else { "No event carries both a last-done date and a sourced interval, so no next date can be computed. That is a gap in the record, not a clean bill." }),
    "",
    "## Retention",
    "",
    "Kept in the vault's reports folder until the next review replaces it; a",
    "superseded review may then be deleted. It carries no identifiers.",
    "",
    "## What this is not",
    "",
    "Date-based items were checked against dated sources. Conditions were **not**",
    "assessed, nothing was examined, and no conclusion about a person was drawn.",
    "The allergy-and-medication check is a word match on what is recorded; it is",
    "not an interaction check, and finding no match clears nothing.",
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
Write-Output "next review: $(if ($nextDue) { $nextDue.ToString('yyyy-MM-dd') } else { 'none computable' })"
Write-Output "report: $reportPath"
