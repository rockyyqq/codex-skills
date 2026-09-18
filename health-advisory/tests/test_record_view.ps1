#Requires -Version 7
$ErrorActionPreference = 'Stop'

$env:HEALTH_VAULT_ROOT = Join-Path $env:TEMP ('hv-view-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $env:HEALTH_VAULT_ROOT 'records') -Force | Out-Null
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

# Markers that must NOT appear in the view: clinical values.
$substanceMarker = 'ZZSUBSTANCE' + [guid]::NewGuid().ToString('N').Substring(0, 6)
$valueMarker = 987.654

Set-VaultRecord -Record @{ schema = 3; as_of = '2026-09-18'; people = @{ 'child-a' = @{
    age_band = '5 years'
    conditions = @(@{ name = 'a condition'; last_confirmed = '2026-09-18'; onset_unknown = $true
                       onset_conflict = $true
                       onset_reports = @(@{ when='2026-01'; informant='parent'; approximate=$true }) })
    medications = @()
    allergies = @(@{ substance = $substanceMarker; reaction = 'x'; last_confirmed = '2026-09-18' })
    family_history = @()
    measurements = @(@{ value = $valueMarker; unit='kg'; taken_on='2026-09-18' })
    treatments_tried = $null
    planned_procedures = @(@{ code='SB708H'; status='booked'; planned_for='2027-02-01'; pre_op_outstanding=$true })
    events = @()
} } }

$view = & pwsh -NoProfile -File (Join-Path $PSScriptRoot '..\scripts\record_view.ps1') 2>&1 | Out-String

Check 'it exits 0' {
    Assert-True ($LASTEXITCODE -eq 0) "exit was $LASTEXITCODE"
}

Check 'it shows section counts' {
    Assert-True ($view -match 'conditions:\s*1') "no condition count: $view"
    Assert-True ($view -match 'planned_procedures:\s*1') "no procedure count: $view"
}

Check 'it shows the flags a decision turns on' {
    Assert-True ($view -match 'onset_unknown=true') "no onset flag: $view"
    Assert-True ($view -match 'severity=ABSENT') "severity absence not shown: $view"
    Assert-True ($view -match 'pre_op_outstanding=true') "pre-op flag not shown: $view"
}

Check 'it names the gaps' {
    Assert-True ($view -match 'treatments_tried not recorded') "treatments gap not named: $view"
    Assert-True ($view -match 'severity not graded') "severity gap not named: $view"
}

Check 'it does NOT leak an allergy substance' {
    Assert-True ($view -notmatch $substanceMarker) 'the view leaked an allergy substance'
}

Check 'it does NOT leak a measurement value' {
    Assert-True ($view -notmatch [string]$valueMarker) 'the view leaked a measurement value'
}

Check 'it does NOT leak a condition name' {
    Assert-True ($view -notmatch 'a condition') 'the view leaked a condition name'
}

Check 'a null section counts as zero, not one' {
    # @($null).Count is 1 in PowerShell. This asserted 1 before and hid the bug.
    $nullDir = Join-Path $env:TEMP ('hv-view-null-' + [guid]::NewGuid().ToString('N'))
    $env:HEALTH_VAULT_ROOT = $nullDir
    New-Item -ItemType Directory -Path (Join-Path $nullDir 'records') -Force | Out-Null
    . (Join-Path $PSScriptRoot '..\scripts\vault.ps1')
    Set-VaultRecord -Record @{ schema = 3; people = @{ 'adult-a' = @{
        conditions = @(); medications = @(); allergies = $null
        treatments_tried = $null; events = @()
    } } }
    $out = & pwsh -NoProfile -File (Join-Path $PSScriptRoot '..\scripts\record_view.ps1') 2>&1 | Out-String
    Assert-True ($out -match 'allergies:\s*0') "a null section should count 0: $out"
    Assert-True ($out -match 'allergies not recorded') "a null section should be named as a gap: $out"
    Remove-Item -LiteralPath $nullDir -Recurse -Force -ErrorAction SilentlyContinue
}

Remove-Item -LiteralPath $env:HEALTH_VAULT_ROOT -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures -gt 0) { Write-Host "`n$($script:Failures) check(s) failed"; exit 1 }
Write-Host "`nall record-view checks passed"; exit 0
