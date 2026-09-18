#Requires -Version 7
$ErrorActionPreference = 'Stop'

$env:HEALTH_VAULT_ROOT = Join-Path $env:TEMP ('hv-due-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $env:HEALTH_VAULT_ROOT 'records') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $env:HEALTH_VAULT_ROOT 'reports') -Force | Out-Null

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

# A record with one overdue item, keyed by a role label we can search for.
$roleLabel = 'zzrole' + [guid]::NewGuid().ToString('N').Substring(0, 6)
Set-VaultRecord -Record @{
    schema = 2
    people = @{ $roleLabel = @{
        conditions  = @()
        medications = @()
        allergies   = @()
        family_history = @()
        measurements   = @()
        # Recorded as "none tried" - not $null, which means "not recorded" and
        # would (correctly) make the whole review CANNOT JUDGE.
        treatments_tried = @()
        events      = @(@{ id = 'E1'; kind = 'screening'; code = 'demo-test'
                           last_done = '2020-01-01'; interval_months = 12; basis = 'fact' })
    } }
}

$dueScript = Join-Path $PSScriptRoot '..\scripts\due_report.ps1'
$stdout = & pwsh -NoProfile -File $dueScript 2>&1 | Out-String
$code = $LASTEXITCODE

Check 'it exits 0' {
    Assert-True ($code -eq 0) "exit was $code"
}

Check 'stdout carries no role label' {
    Assert-True ($stdout -notmatch $roleLabel) 'stdout leaked a role label from the record'
}

Check 'it reports a DUE status' {
    Assert-True ($stdout -match 'status:\s*DUE') "stdout did not report 'status: DUE': $stdout"
}

Check 'it wrote a report file' {
    $files = @(Get-ChildItem (Join-Path $env:HEALTH_VAULT_ROOT 'reports') -Filter '*-review.md')
    Assert-True ($files.Count -ge 1) 'no review file was written'
}

Check 'the written report names the overdue item' {
    $files = @(Get-ChildItem (Join-Path $env:HEALTH_VAULT_ROOT 'reports') -Filter '*-review.md')
    $body = Get-Content -LiteralPath $files[0].FullName -Raw
    Assert-True ($body -match 'demo-test') 'the report does not name the overdue item'
}

Check 'an unrecorded field makes the review CANNOT JUDGE, not DUE' {
    $incomplete = Join-Path $env:TEMP ('hv-inc-' + [guid]::NewGuid().ToString('N'))
    $env:HEALTH_VAULT_ROOT = $incomplete
    New-Item -ItemType Directory -Path (Join-Path $incomplete 'records') -Force | Out-Null
    . (Join-Path $PSScriptRoot '..\scripts\vault.ps1')
    Set-VaultRecord -Record @{
        schema = 3
        people = @{ 'child-a' = @{
            conditions = @(); medications = @(); allergies = @()
            family_history = @(); measurements = @()
            treatments_tried = $null
            events = @()
        } }
    }
    $out = & pwsh -NoProfile -File (Join-Path $PSScriptRoot '..\scripts\due_report.ps1') 2>&1 | Out-String
    Assert-True ($out -match 'status:\s*CANNOT JUDGE') "expected CANNOT JUDGE, got: $out"
    Assert-True ($out -match 'cannot judge:\s*[1-9]') "the unknown was not counted: $out"
    Remove-Item -LiteralPath $incomplete -Recurse -Force -ErrorAction SilentlyContinue
}

Check 'several items render as a list, not System.Object[]' {
    # A single element unwraps to a scalar and hides this bug.
    $multi = Join-Path $env:TEMP ('hv-multi-' + [guid]::NewGuid().ToString('N'))
    $env:HEALTH_VAULT_ROOT = $multi
    New-Item -ItemType Directory -Path (Join-Path $multi 'records') -Force | Out-Null
    . (Join-Path $PSScriptRoot '..\scripts\vault.ps1')
    Set-VaultRecord -Record @{ schema = 3; people = @{ 'adult-a' = @{
        conditions = @(); medications = @(); allergies = @()
        family_history = @(); measurements = @()
        treatments_tried = @()
        events = @(
            @{ id='E1'; kind='screening'; code='alpha'; last_done='2020-01-01'; interval_months=12; basis='fact' }
            @{ id='E2'; kind='screening'; code='beta';  last_done='2020-01-01'; interval_months=12; basis='fact' }
        )
    } } }
    $dir = Join-Path $env:HEALTH_VAULT_ROOT 'reports'
    & pwsh -NoProfile -File (Join-Path $PSScriptRoot '..\scripts\due_report.ps1') > $null 2>&1
    $file = @(Get-ChildItem $dir -Filter '*-review.md')[0]
    $body = Get-Content -LiteralPath $file.FullName -Raw
    Assert-True ($body -notmatch 'System\.Object') "the report rendered an array object: $body"
    Assert-True ($body -match 'alpha') 'the first item is missing'
    Assert-True ($body -match 'beta')  'the second item is missing'
    Remove-Item -LiteralPath $multi -Recurse -Force -ErrorAction SilentlyContinue
}

Remove-Item -LiteralPath $env:HEALTH_VAULT_ROOT -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures -gt 0) { Write-Host "`n$($script:Failures) check(s) failed"; exit 1 }
Write-Host "`nall due-report checks passed"; exit 0
