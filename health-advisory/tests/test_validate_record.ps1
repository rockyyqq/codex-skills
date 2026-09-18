#Requires -Version 7
$ErrorActionPreference = 'Stop'

$env:HEALTH_VAULT_ROOT = Join-Path $env:TEMP ('hv-val-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $env:HEALTH_VAULT_ROOT 'records') -Force | Out-Null
$env:PYTHONUTF8 = '1'
. (Join-Path $PSScriptRoot '..\scripts\vault.ps1')

$validator = Join-Path $PSScriptRoot '..\scripts\validate_record.ps1'
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

function GoodRecord {
    @{ schema = 3; as_of = '2026-09-18'; people = @{ 'child-a' = @{
        conditions  = @(@{ name = 'x'; last_confirmed = '2026-09-18' })
        medications = @()
        allergies   = @()
        events      = @()
    } } }
}

Check 'a schema-valid record passes' {
    Set-VaultRecord -Record (GoodRecord)
    $out = & pwsh -NoProfile -File $validator 2>&1 | Out-String
    Assert-True ($LASTEXITCODE -eq 0) "exit was $LASTEXITCODE : $out"
}

Check 'a misspelled key is refused' {
    $bad = GoodRecord
    $bad['people']['child-a']['planned_procedure'] = @(@{ code = 'X' })
    Set-VaultRecord -Record $bad
    $out = & pwsh -NoProfile -File $validator 2>&1 | Out-String
    Assert-True ($LASTEXITCODE -eq 1) "exit was $LASTEXITCODE : $out"
    Assert-True ($out -match 'planned_procedure') "did not name the bad key: $out"
}

Check 'a missing required key is refused' {
    $bad = GoodRecord
    $bad['people']['child-a'].Remove('medications')
    Set-VaultRecord -Record $bad
    $out = & pwsh -NoProfile -File $validator 2>&1 | Out-String
    Assert-True ($LASTEXITCODE -eq 1) "exit was $LASTEXITCODE"
    Assert-True ($out -match 'medications') "did not name the missing key: $out"
}

Check 'a person key that is not a role label is refused' {
    $bad = GoodRecord
    $bad['people']['Jane'] = $bad['people']['child-a']
    $bad['people'].Remove('child-a')
    Set-VaultRecord -Record $bad
    $out = & pwsh -NoProfile -File $validator 2>&1 | Out-String
    # Asserting the exit code alone is not enough: a crash also exits 1.
    Assert-True ($LASTEXITCODE -eq 1) "exit was $LASTEXITCODE"
    Assert-True ($out -match 'not a role label') "did not name the reason: $out"
    Assert-True ($out -notmatch 'cannot be retrieved') "the script crashed instead of reporting: $out"
}

Check 'an unsupported schema version is refused' {
    $bad = GoodRecord
    $bad['schema'] = 99
    Set-VaultRecord -Record $bad
    $out = & pwsh -NoProfile -File $validator 2>&1 | Out-String
    Assert-True ($LASTEXITCODE -eq 1) "exit was $LASTEXITCODE"
    Assert-True ($out -match 'unsupported schema') "did not name the version: $out"
}

Check 'a bad onset report key is refused' {
    $bad = GoodRecord
    $bad['people']['child-a']['conditions'][0]['onset_reports'] = @(@{ when = '2026-01'; informant = 'parent'; approximate = $true; guess = 'x' })
    Set-VaultRecord -Record $bad
    $out = & pwsh -NoProfile -File $validator 2>&1 | Out-String
    Assert-True ($LASTEXITCODE -eq 1) "exit was $LASTEXITCODE"
    Assert-True ($out -match 'guess') "did not name the bad key: $out"
}

Remove-Item -LiteralPath $env:HEALTH_VAULT_ROOT -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures -gt 0) { Write-Host "`n$($script:Failures) check(s) failed"; exit 1 }
Write-Host "`nall record-validation checks passed"; exit 0
