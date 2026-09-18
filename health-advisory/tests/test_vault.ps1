#Requires -Version 7
$ErrorActionPreference = 'Stop'

# Isolate the vault: a test must never touch the real record.
$env:HEALTH_VAULT_ROOT = Join-Path $env:TEMP ('hv-test-' + [guid]::NewGuid().ToString('N'))
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

$marker = 'ZZPROBE' + [guid]::NewGuid().ToString('N')

Check 'round-trip returns the record' {
    $sample = @{
        schema = 2
        people = @{ 'adult-a' = @{
            conditions  = @()
            allergies   = @()
            events      = @()
            medications = @(@{ name = $marker; source = 'label' })
        } }
    }
    Set-VaultRecord -Record $sample
    $back = Get-VaultRecord
    Assert-True ($back['people']['adult-a']['medications'][0]['name'] -eq $marker) 'round-trip mismatch'
}

Check 'the file on disk does not contain the plaintext' {
    $raw = Get-Content -LiteralPath $script:RecordFile -Raw
    Assert-True ($raw -notmatch [regex]::Escape($marker)) 'plaintext found on disk'
}

Check 'status reports counts and leaks no content' {
    $status = Get-VaultStatus | Out-String
    Assert-True ($status -notmatch [regex]::Escape($marker)) 'status leaked record content'
    Assert-True ($status -match 'People') 'status did not report a people count'
}

Check 'a missing boundary file refuses to run' {
    $saved = $script:BoundaryFile
    $script:BoundaryFile = Join-Path $env:TEMP 'hv-no-such-boundary.md'
    try {
        try { Get-VaultRecord | Out-Null; throw 'expected a refusal, got a result' }
        catch { Assert-True ($_.Exception.Message -like 'REFUSING*') "wrong error: $($_.Exception.Message)" }
    } finally { $script:BoundaryFile = $saved }
}

Remove-Item -LiteralPath $env:HEALTH_VAULT_ROOT -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures -gt 0) { Write-Host "`n$($script:Failures) check(s) failed"; exit 1 }
Write-Host "`nall vault checks passed"; exit 0
