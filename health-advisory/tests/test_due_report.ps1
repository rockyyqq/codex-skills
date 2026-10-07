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

# A person with every section present. Each fixture overrides only what it tests,
# so adding a section to the schema updates one place instead of turning every
# fixture into an incomplete record and failing the suite for the wrong reason.
function Complete-Person {
    param([hashtable]$Overrides = @{})
    $person = @{
        relationship     = 'self'
        conditions       = @()
        medications      = @()
        allergies        = @()
        family_history   = @()
        measurements     = @()
        lifestyle        = @()
        treatments_tried = @()
        planned_procedures = @()
        events           = @()
    }
    foreach ($key in $Overrides.Keys) { $person[$key] = $Overrides[$key] }
    return $person
}

# A record with one overdue item, keyed by a role label we can search for.
$roleLabel = 'zzrole' + [guid]::NewGuid().ToString('N').Substring(0, 6)
Set-VaultRecord -Record @{
    schema = 3
    people = @{ $roleLabel = (Complete-Person @{
        events = @(@{ id = 'E1'; kind = 'screening'; code = 'demo-test'
                      last_done = '2020-01-01'; interval_months = 12; basis = 'fact' })
    }) }
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

Check 'the report states a retention and the next review date' {
    $files = @(Get-ChildItem (Join-Path $env:HEALTH_VAULT_ROOT 'reports') -Filter '*-review.md')
    $body = Get-Content -LiteralPath $files[0].FullName -Raw
    Assert-True ($body -match '## Retention') 'the report does not state a retention'
    Assert-True ($body -match '## Next review') 'the report does not state the next review'
}

Check 'the next review date comes from the sourced interval, not the calendar' {
    # The fixture's item was last done 2020-01-01 with a 12-month interval, so it
    # is overdue and no future date exists. A second, future-dated item proves the
    # date is computed rather than assumed from today.
    $future = Join-Path $env:TEMP ('hv-future-' + [guid]::NewGuid().ToString('N'))
    $env:HEALTH_VAULT_ROOT = $future
    New-Item -ItemType Directory -Path (Join-Path $future 'records') -Force | Out-Null
    . (Join-Path $PSScriptRoot '..\scripts\vault.ps1')
    Set-VaultRecord -Record @{ schema = 3; people = @{ 'adult-a' = (Complete-Person @{
        events = @(@{ id='E9'; kind='screening'; code='future-test'
                      last_done = '2026-08-01'; interval_months = 12; basis = 'fact' })
    }) } }
    $out = & pwsh -NoProfile -File $dueScript 2>&1 | Out-String
    Assert-True ($out -match 'next review:\s*2027-08-01') "expected the computed date, got: $out"
    Remove-Item -LiteralPath $future -Recurse -Force -ErrorAction SilentlyContinue
}

Check 'an allergy and a medication sharing a word become a fact' {
    $share = Join-Path $env:TEMP ('hv-share-' + [guid]::NewGuid().ToString('N'))
    $env:HEALTH_VAULT_ROOT = $share
    New-Item -ItemType Directory -Path (Join-Path $share 'records') -Force | Out-Null
    . (Join-Path $PSScriptRoot '..\scripts\vault.ps1')
    $word = 'zz' + [guid]::NewGuid().ToString('N').Substring(0, 8)
    Set-VaultRecord -Record @{ schema = 3; people = @{ 'adult-a' = (Complete-Person @{
        allergies   = @(@{ substance = $word; reaction = 'a rash'; last_confirmed = '2026-09-18' })
        medications = @(@{ name = $word; source = 'memory' })
    }) } }
    $out = & pwsh -NoProfile -File $dueScript 2>&1 | Out-String
    Assert-True ($out -match 'status:\s*DUE') "the shared word did not raise a fact: $out"
    Assert-True ($out -notmatch $word) 'stdout leaked the shared word itself'
    $files = @(Get-ChildItem (Join-Path $share 'reports') -Filter '*-review.md')
    $body = Get-Content -LiteralPath $files[0].FullName -Raw
    Assert-True ($body -match $word) 'the report did not name the shared word'
    Remove-Item -LiteralPath $share -Recurse -Force -ErrorAction SilentlyContinue
}

Check 'a placeholder allergy is not matched against anything' {
    # "no known drug allergies" is a placeholder, not a substance. Matching it
    # would put a false fact in the review and teach the reader to distrust it.
    $placeholder = Join-Path $env:TEMP ('hv-ph-' + [guid]::NewGuid().ToString('N'))
    $env:HEALTH_VAULT_ROOT = $placeholder
    New-Item -ItemType Directory -Path (Join-Path $placeholder 'records') -Force | Out-Null
    . (Join-Path $PSScriptRoot '..\scripts\vault.ps1')
    Set-VaultRecord -Record @{ schema = 3; people = @{ 'child-a' = (Complete-Person @{
        allergies   = @(@{ substance = 'no known drug allergies'; reaction = 'not applicable'; last_confirmed = '2026-09-18' })
        medications = @(@{ name = 'vonoprazan'; source = 'label' })
    }) } }
    $out = & pwsh -NoProfile -File $dueScript 2>&1 | Out-String
    Assert-True ($out -match 'status:\s*OK') "a placeholder produced a fact: $out"
    Remove-Item -LiteralPath $placeholder -Recurse -Force -ErrorAction SilentlyContinue
}

Check 'an unrecorded field makes the review CANNOT JUDGE, not DUE' {
    $incomplete = Join-Path $env:TEMP ('hv-inc-' + [guid]::NewGuid().ToString('N'))
    $env:HEALTH_VAULT_ROOT = $incomplete
    New-Item -ItemType Directory -Path (Join-Path $incomplete 'records') -Force | Out-Null
    . (Join-Path $PSScriptRoot '..\scripts\vault.ps1')
    Set-VaultRecord -Record @{
        schema = 3
        people = @{ 'child-a' = (Complete-Person @{ treatments_tried = $null }) }
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
    Set-VaultRecord -Record @{ schema = 3; people = @{ 'adult-a' = (Complete-Person @{
        events = @(
            @{ id='E1'; kind='screening'; code='alpha'; last_done='2020-01-01'; interval_months=12; basis='fact' }
            @{ id='E2'; kind='screening'; code='beta';  last_done='2020-01-01'; interval_months=12; basis='fact' }
        )
    }) } }
    $dir = Join-Path $env:HEALTH_VAULT_ROOT 'reports'
    & pwsh -NoProfile -File (Join-Path $PSScriptRoot '..\scripts\due_report.ps1') > $null 2>&1
    $file = @(Get-ChildItem $dir -Filter '*-review.md')[0]
    $body = Get-Content -LiteralPath $file.FullName -Raw
    Assert-True ($body -notmatch 'System\.Object') "the report rendered an array object: $body"
    Assert-True ($body -match 'alpha') 'the first item is missing'
    Assert-True ($body -match 'beta')  'the second item is missing'
    Remove-Item -LiteralPath $multi -Recurse -Force -ErrorAction SilentlyContinue
}

Check 'a null events section does not crash the review' {
    # @($null) is one null element, so the loop body ran once on $null and threw.
    $nullEvents = Join-Path $env:TEMP ('hv-nullev-' + [guid]::NewGuid().ToString('N'))
    $env:HEALTH_VAULT_ROOT = $nullEvents
    New-Item -ItemType Directory -Path (Join-Path $nullEvents 'records') -Force | Out-Null
    . (Join-Path $PSScriptRoot '..\scripts\vault.ps1')
    Set-VaultRecord -Record @{ schema = 3; people = @{ 'adult-b' = (Complete-Person @{ events = $null }) } }
    $out = & pwsh -NoProfile -File (Join-Path $PSScriptRoot '..\scripts\due_report.ps1') 2>&1 | Out-String
    Assert-True ($out -notmatch 'Cannot index into a null array') "the review crashed: $out"
    Assert-True ($out -match 'status:') "the review produced no status: $out"
    Remove-Item -LiteralPath $nullEvents -Recurse -Force -ErrorAction SilentlyContinue
}

Remove-Item -LiteralPath $env:HEALTH_VAULT_ROOT -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures -gt 0) { Write-Host "`n$($script:Failures) check(s) failed"; exit 1 }
Write-Host "`nall due-report checks passed"; exit 0
