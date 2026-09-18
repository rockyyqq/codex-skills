#Requires -Version 7
<#
  The only component that touches vault ciphertext.
  Deliberately exposes no command that prints record content.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:VaultRoot = if ($env:HEALTH_VAULT_ROOT) { $env:HEALTH_VAULT_ROOT }
                    else { 'C:\Users\yuanq\Desktop\chatgpt folder\health-vault' }
$script:BoundaryFile = Join-Path $PSScriptRoot '..\references\boundary-and-privacy.md'
$script:RecordFile   = Join-Path $script:VaultRoot 'records\household_health.json'

function Assert-Boundary {
    if (-not (Test-Path -LiteralPath $script:BoundaryFile)) {
        throw "REFUSING TO RUN: boundary-and-privacy.md is missing at $($script:BoundaryFile)"
    }
}

function Protect-Text {
    param([Parameter(Mandatory)][string]$Text)
    Add-Type -AssemblyName System.Security
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $enc = [System.Security.Cryptography.ProtectedData]::Protect($bytes, $null, 'CurrentUser')
    [Convert]::ToBase64String($enc)
}

function Unprotect-Text {
    param([Parameter(Mandatory)][string]$Base64)
    Add-Type -AssemblyName System.Security
    $enc = [Convert]::FromBase64String($Base64)
    $bytes = [System.Security.Cryptography.ProtectedData]::Unprotect($enc, $null, 'CurrentUser')
    [System.Text.Encoding]::UTF8.GetString($bytes)
}

function Get-VaultRecord {
    Assert-Boundary
    if (-not (Test-Path -LiteralPath $script:RecordFile)) { return $null }
    $b64 = (Get-Content -LiteralPath $script:RecordFile -Raw).Trim()
    Unprotect-Text -Base64 $b64 | ConvertFrom-Json -AsHashtable
}

function Set-VaultRecord {
    param([Parameter(Mandatory)]$Record)
    Assert-Boundary
    $json = $Record | ConvertTo-Json -Depth 12
    $dir = Split-Path -Parent $script:RecordFile
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-Content -LiteralPath $script:RecordFile -Value (Protect-Text -Text $json) -NoNewline
}

function Get-VaultStatus {
    Assert-Boundary
    $exists = Test-Path -LiteralPath $script:RecordFile
    $people = 0; $meds = 0; $conditions = 0; $events = 0
    if ($exists) {
        $record = Get-VaultRecord
        if ($record -and $record['people']) {
            $people = $record['people'].Keys.Count
            foreach ($key in $record['people'].Keys) {
                $person = $record['people'][$key]
                if ($person['medications']) { $meds += @($person['medications']).Count }
                if ($person['conditions'])  { $conditions += @($person['conditions']).Count }
                if ($person['events'])      { $events += @($person['events']).Count }
            }
        }
    }
    [pscustomobject]@{
        Backend       = 'DPAPI (CurrentUser)'
        RecordPath    = $script:RecordFile
        Exists        = $exists
        LastWriteTime = if ($exists) { (Get-Item -LiteralPath $script:RecordFile).LastWriteTime.ToString('s') } else { $null }
        People        = $people
        Medications   = $meds
        Conditions    = $conditions
        Events        = $events
    }
}

# CLI entry point. Only 'status' exists: there is deliberately no command that
# prints record content, because stdout is persisted by the session store.
if ($MyInvocation.InvocationName -ne '.' -and $args.Count -ge 1) {
    switch ($args[0]) {
        'status' { Get-VaultStatus | Format-List; exit 0 }
        # Console.Error, not Write-Error: with ErrorActionPreference 'Stop',
        # Write-Error throws before the exit code is reached.
        default  {
            [Console]::Error.WriteLine("Unknown command '$($args[0])'. Only 'status' exists.")
            exit 2
        }
    }
}
