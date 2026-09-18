#Requires -Version 7
<#
  Validates the stored record against the schema in references/record-fields.md.

  It fails closed on any unknown key. A misspelled key makes a real item
  invisible - the review then reports a false all-clear, which is worse than a
  crash. This script is the thing that turns that silence into a refusal.

  It prints key paths and identifiers only. Record content never reaches stdout,
  because stdout is persisted by the session store.
#>
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'vault.ps1')

$SUPPORTED_SCHEMA = @(3)

$KNOWN_TOP        = @('schema', 'as_of', 'people')
$REQUIRED_TOP     = @('schema', 'people')
$KNOWN_PERSON     = @('age_band', 'conditions', 'medications', 'allergies', 'family_history',
                      'measurements', 'treatments_tried', 'treatments_tried_note',
                      'planned_procedures', 'events')
$REQUIRED_PERSON  = @('conditions', 'medications', 'allergies')
$KNOWN_CONDITION  = @('name', 'last_confirmed', 'onset_reports', 'onset_unknown', 'onset_conflict', 'severity')
$REQUIRED_CONDITION = @('name', 'last_confirmed')
$KNOWN_ONSET      = @('when', 'precision', 'informant', 'approximate', 'note')
$REQUIRED_ONSET   = @('when', 'informant', 'approximate')
$KNOWN_MEDICATION = @('name', 'source', 'dose_text', 'prescriber', 'started', 'stopped', 'stop_reason')
$REQUIRED_MEDICATION = @('name', 'source')
$KNOWN_ALLERGY    = @('substance', 'reaction', 'last_confirmed')
$REQUIRED_ALLERGY = @('substance', 'reaction', 'last_confirmed')
$KNOWN_FAMILY     = @('relative', 'condition', 'age_at_diagnosis', 'side')
$REQUIRED_FAMILY  = @('relative', 'condition')
$KNOWN_MEASURE    = @('value', 'unit', 'taken_on', 'reference_range', 'conditions_of_measurement')
$REQUIRED_MEASURE = @('value', 'unit', 'taken_on')
$KNOWN_PROCEDURE  = @('code', 'status', 'planned_for', 'pre_op_outstanding', 'name', 'tosp_table', 'setting', 'source')
$REQUIRED_PROCEDURE = @('code', 'status', 'planned_for', 'pre_op_outstanding')
$KNOWN_EVENT      = @('id', 'kind', 'code', 'last_done', 'interval_months', 'basis', 'source_id')
$REQUIRED_EVENT   = @('id', 'kind', 'code', 'last_done', 'interval_months', 'basis', 'source_id')

$problems = [System.Collections.Generic.List[string]]::new()

function Test-Keys {
    param($Object, [string[]]$Known, [string[]]$Required, [string]$Where)
    if ($null -eq $Object) { return }
    foreach ($key in $Object.Keys) {
        if ($Known -notcontains $key) { $problems.Add("${Where}: unknown key '${key}'") }
    }
    foreach ($key in $Required) {
        if (-not $Object.ContainsKey($key)) { $problems.Add("${Where}: missing required key '${key}'") }
    }
}

$record = Get-VaultRecord
if ($null -eq $record) {
    Write-Output 'no record stored yet - nothing to validate'
    exit 0
}

Test-Keys -Object $record -Known $KNOWN_TOP -Required $REQUIRED_TOP -Where 'document'

if ($record.ContainsKey('schema')) {
    if ($SUPPORTED_SCHEMA -notcontains [int]$record['schema']) {
        $problems.Add("document: unsupported schema version '$($record['schema'])'")
    }
}

if ($record.ContainsKey('people')) {
    foreach ($personKey in @($record['people'].Keys)) {
        if ($personKey -notmatch '^(adult|child)-[a-z]$') {
            $problems.Add("people: '${personKey}' is not a role label (expected adult-x or child-x)")
        }
        $person = $record['people'][$personKey]
        Test-Keys -Object $person -Known $KNOWN_PERSON -Required $REQUIRED_PERSON -Where $personKey

        foreach ($section in @(
            @{ name = 'conditions';       known = $KNOWN_CONDITION;  required = $REQUIRED_CONDITION }
            @{ name = 'medications';      known = $KNOWN_MEDICATION; required = $REQUIRED_MEDICATION }
            @{ name = 'allergies';        known = $KNOWN_ALLERGY;    required = $REQUIRED_ALLERGY }
            @{ name = 'family_history';   known = $KNOWN_FAMILY;     required = $REQUIRED_FAMILY }
            @{ name = 'measurements';     known = $KNOWN_MEASURE;    required = $REQUIRED_MEASURE }
            @{ name = 'planned_procedures'; known = $KNOWN_PROCEDURE; required = $REQUIRED_PROCEDURE }
            @{ name = 'events';           known = $KNOWN_EVENT;      required = $REQUIRED_EVENT }
        )) {
            # Hashtable access must use ['key'] - under StrictMode, .key throws.
            $sectionName = $section['name']
            $items = @($person[$sectionName])
            if ($items.Count -eq 0) { continue }
            for ($i = 0; $i -lt $items.Count; $i++) {
                $item = $items[$i]
                if ($null -eq $item) { continue }
                Test-Keys -Object $item -Known $section['known'] -Required $section['required'] `
                          -Where "${personKey}/${sectionName}[$i]"

                if ($sectionName -eq 'conditions') {
                    $reports = @($item['onset_reports'])
                    for ($j = 0; $j -lt $reports.Count; $j++) {
                        if ($null -eq $reports[$j]) { continue }
                        Test-Keys -Object $reports[$j] -Known $KNOWN_ONSET -Required $REQUIRED_ONSET `
                                  -Where "${personKey}/conditions[$i]/onset_reports[$j]"
                    }
                }
            }
        }
    }
}

if ($problems.Count -gt 0) {
    Write-Output "FAIL: $($problems.Count) problem(s) in the stored record"
    foreach ($problem in $problems) { Write-Output "  $problem" }
    exit 1
}
Write-Output 'OK: the stored record matches the schema'
exit 0
