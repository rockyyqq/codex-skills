#Requires -Version 7
<#
  Asserts the stored record carries no identifiers.

  It prints pass/fail only: the record's content never reaches stdout, because
  stdout is persisted by the session store.
#>
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\scripts\vault.ps1')

$script:Failures = 0
function Check {
    param([string]$Name, [scriptblock]$Body)
    try { & $Body; Write-Host "PASS  $Name" }
    catch { Write-Host "FAIL  $Name :: $($_.Exception.Message)"; $script:Failures++ }
}
function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

$record = Get-VaultRecord
if (-not $record) {
    Write-Host "no record stored yet - nothing to check"
    exit 0
}

$json = $record | ConvertTo-Json -Depth 12

# Identifier shapes the schema forbids.
$patterns = @{
    'national ID'  = '\b[STFG]\d{7}[A-Z]\b'
    'email'        = '[\w.+-]+@[\w-]+\.[\w.]+'
    'phone'        = '\b(?:\+65|65)?\s?[689]\d{3}\s?\d{4}\b'
    'full DOB'     = '\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:19|20)\d{2}\b'
    'account no.'  = '\bACCOUNT\s*NO|\baccount_number\b'
    'a dose field' = '"dose"\s*:'
}

foreach ($label in $patterns.Keys) {
    Check "the record carries no $label" {
        Assert-True ($json -notmatch $patterns[$label]) "found a $label pattern in the stored record"
    }
}

Check 'people are keyed by role label, not a name' {
    $keys = @($record['people'].Keys)
    foreach ($key in $keys) {
        Assert-True ($key -match '^(adult|child)-[a-z]$') "person key '$key' is not a role label"
    }
}

if ($script:Failures -gt 0) { Write-Host "`n$($script:Failures) check(s) failed"; exit 1 }
Write-Host "`nall record-privacy checks passed"; exit 0
