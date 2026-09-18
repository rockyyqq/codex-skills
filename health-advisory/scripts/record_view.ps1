#Requires -Version 7
<#
  A derived view of the stored record: its structure, its flags and its gaps.

  It exists because analysing a record from memory of having written it is not
  analysis - it is recollection. This is the artifact you read back instead.

  What it emits: section counts, key presence, dates, conflict flags, codes.
  What it does NOT emit: condition names, allergy substances, measurement
  values, family detail. Those never reach stdout, because stdout is persisted
  by the session store.
#>
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'vault.ps1')
. (Join-Path $PSScriptRoot 'record_gaps.ps1')

$record = Get-VaultRecord
if ($null -eq $record) { Write-Output 'no record stored yet'; exit 0 }

function Show-Value {
    param($Value, [string]$Label)
    if ($null -eq $Value) { return "${Label}=ABSENT" }
    if ($Value -is [bool]) { return "${Label}=$(if ($Value) {'true'} else {'false'})" }
    return "${Label}=$Value"
}

# @($null).Count is 1, not 0 - so a null section would report as one item.
function Count-Items {
    param($Value)
    if ($null -eq $Value) { return 0 }
    return @($Value).Count
}

Write-Output "schema: $($record['schema'])  as_of: $($record['as_of'])"

foreach ($personKey in @($record['people'].Keys)) {
    $person = $record['people'][$personKey]
    Write-Output ""
    # The label alone means nothing; the relationship is what makes it readable.
    $who = if ($person['relationship']) { $person['relationship'] } else { 'relationship NOT RECORDED' }
    Write-Output "person: $personKey ($who)"
    Write-Output "  age_band: $(if ($person['age_band']) { 'present' } else { 'ABSENT' })"

    foreach ($section in @('conditions', 'medications', 'allergies', 'family_history', 'measurements', 'planned_procedures', 'events')) {
        Write-Output "  ${section}: $(Count-Items $person[$section])"
    }

    # Conditions: flags and dates only, never the name.
    $ci = 0
    foreach ($condition in @($person['conditions'])) {
        if (-not $condition) { continue }
        $flags = @(
            (Show-Value $condition['last_confirmed'] 'last_confirmed')
            "onset_reports=$(Count-Items $condition['onset_reports'])"
            (Show-Value $condition['onset_unknown'] 'onset_unknown')
            (Show-Value $condition['onset_conflict'] 'onset_conflict')
            (Show-Value $condition['severity'] 'severity')
        )
        Write-Output "    conditions[$ci]: $($flags -join ' ')"
        $ci++
    }

    # Planned procedures: the code is needed to act on, so it is shown.
    $pi = 0
    foreach ($procedure in @($person['planned_procedures'])) {
        if (-not $procedure) { continue }
        $flags = @(
            (Show-Value $procedure['code'] 'code')
            (Show-Value $procedure['status'] 'status')
            (Show-Value $procedure['planned_for'] 'planned_for')
            (Show-Value $procedure['pre_op_outstanding'] 'pre_op_outstanding')
        )
        Write-Output "    planned_procedures[$pi]: $($flags -join ' ')"
        $pi++
    }

    # The gaps, in one line, so a reader cannot mistake a thin record for a clean one.
    $gaps = Get-RecordGaps -Person $person
    Write-Output "  gaps: $(if ($gaps.Count) { $gaps -join '; ' } else { 'none detected' })"
}
exit 0
