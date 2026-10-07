#Requires -Version 7
<#
  Checks for vault_backup.ps1. Every guard is proved to fail, not asserted to pass.

  It never touches the real vault or the real backup folder: everything happens
  under HEALTH_VAULT_ROOT in the temp directory, and the passphrase is a test
  passphrase that is not the household's.
#>
$ErrorActionPreference = 'Stop'

$env:HEALTH_VAULT_ROOT = Join-Path $env:TEMP ('hv-backup-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $env:HEALTH_VAULT_ROOT 'records') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $env:HEALTH_VAULT_ROOT 'reports') -Force | Out-Null

. (Join-Path $PSScriptRoot '..\scripts\vault_backup.ps1')

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

$marker = 'ZZBACKUP' + [guid]::NewGuid().ToString('N')
$pass   = 'test-only-passphrase-' + [guid]::NewGuid().ToString('N')
$dest   = Join-Path $env:TEMP ('hv-dest-' + [guid]::NewGuid().ToString('N'))

# A record whose content is recognisable after a restore.
$sample = @{
    schema = 3
    as_of  = '2026-09-18'
    people = @{ 'adult-a' = @{
        conditions = @(@{ name = $marker; last_confirmed = '2026-09-18' })
        medications = @(); allergies = @(); lifestyle = @(); measurements = @()
        events = @(); treatments_tried = @(); planned_procedures = @(); family_history = @()
    } }
}
Set-VaultRecord -Record $sample
Set-Content -LiteralPath (Join-Path $env:HEALTH_VAULT_ROOT 'records\emergency-card.md') -Value 'card text' -Encoding utf8
Set-Content -LiteralPath (Join-Path $env:HEALTH_VAULT_ROOT 'reports\2026-09-18-review.md') -Value 'review text' -Encoding utf8

$script:result = $null

Check 'export writes a container and passes its own restore drill' {
    $script:result = Export-VaultBackup -Destination $dest -Passphrase $pass
    Assert-True (Test-Path -LiteralPath $script:result.Path) 'no file was written'
    Assert-True ($script:result.SelfTest -eq 'OK') "the restore drill did not pass: $($script:result.SelfTest)"
}

Check 'the container does not carry the record in plaintext' {
    $bytes = [System.IO.File]::ReadAllBytes($script:result.Path)
    $text = [System.Text.Encoding]::UTF8.GetString($bytes)
    Assert-True ($text -notmatch [regex]::Escape($marker)) 'plaintext found in the container'
}

Check 'the container carries its own key derivation, so it is portable' {
    $bytes = [System.IO.File]::ReadAllBytes($script:result.Path)
    Assert-True ([System.Text.Encoding]::ASCII.GetString($bytes, 0, 5) -eq 'HVBK1') 'wrong magic'
    Assert-True ([int]$bytes[5] -eq 1) 'unexpected key-derivation id'
    Assert-True ([System.BitConverter]::ToInt32($bytes, 6) -eq 600000) 'iteration count not recorded'
}

Check 'verify reports counts and writes nothing' {
    $before = (Get-Item -LiteralPath $script:RecordFile).LastWriteTimeUtc
    $info = Test-VaultBackup -Path $script:result.Path -Passphrase $pass
    Assert-True ($info.People -eq 1) "people count wrong: $($info.People)"
    Assert-True ($info.Files -eq 2) "file count wrong: $($info.Files)"
    Assert-True ((Get-Item -LiteralPath $script:RecordFile).LastWriteTimeUtc -eq $before) 'verify touched the record'
}

Check 'export claims no passphrase copy when none was asked for' {
    $r = Export-VaultBackup -Destination $dest -Passphrase $pass
    Assert-True (-not $r.PassphraseCopy) "unexpected passphrase copy: $($r.PassphraseCopy)"
}

Check 'a requested passphrase copy is written, for the current user only' {
    $copyPath = Join-Path $env:TEMP ('hv-pass-' + [guid]::NewGuid().ToString('N') + '.txt')
    $r = Export-VaultBackup -Destination $dest -Passphrase $pass -PassphraseFile $copyPath
    Assert-True (Test-Path -LiteralPath $copyPath) 'no passphrase copy was written'
    Assert-True ((Get-Content -LiteralPath $copyPath -Raw).Contains($pass)) 'the copy does not contain the passphrase'
    $rules = @((Get-Acl -LiteralPath $copyPath).Access | Where-Object { -not $_.IsInherited })
    Assert-True ($rules.Count -eq 1) "expected one access rule on the copy, found $($rules.Count)"
    Assert-True ($rules[0].IdentityReference.Value -eq [System.Security.Principal.WindowsIdentity]::GetCurrent().Name) "the rule is not for the current user: $($rules[0].IdentityReference.Value)"
    Remove-Item -LiteralPath $copyPath -Force
}

Check 'a wrong passphrase is refused' {
    $other = 'not-the-passphrase-' + [guid]::NewGuid().ToString('N')
    $threw = $false
    try { Test-VaultBackup -Path $script:result.Path -Passphrase $other | Out-Null } catch { $threw = $true }
    Assert-True $threw 'a wrong passphrase was accepted'
}

Check 'a restore how-to sits beside the container and carries no passphrase' {
    # In two years nobody opening the file will know it needs PowerShell 7, or
    # what to type. The instructions have to travel with the container.
    $howto = Join-Path (Split-Path -Parent $script:result.Path) 'RESTORE-HOWTO.txt'
    Assert-True (Test-Path -LiteralPath $howto) 'no restore how-to was written'
    $text = Get-Content -LiteralPath $howto -Raw
    Assert-True ($text -match 'PowerShell 7') 'the how-to does not name the PowerShell requirement'
    Assert-True ($text -match 'restore') 'the how-to does not explain restoring'
    Assert-True (-not $text.Contains($pass)) 'the how-to contains the passphrase'
}

Check 'a single flipped byte is refused' {
    $copy = Join-Path $dest 'tampered.enc'
    $bytes = [System.IO.File]::ReadAllBytes($script:result.Path)
    $bytes[$bytes.Length - 20] = $bytes[$bytes.Length - 20] -bxor 1
    [System.IO.File]::WriteAllBytes($copy, $bytes)
    $threw = $false
    try { Test-VaultBackup -Path $copy -Passphrase $pass | Out-Null } catch { $threw = $true }
    Assert-True $threw 'a tampered container was accepted'
}

Check 'a truncated file is refused' {
    $copy = Join-Path $dest 'truncated.enc'
    $bytes = [System.IO.File]::ReadAllBytes($script:result.Path)
    $short = [byte[]]::new(40)
    [Array]::Copy($bytes, $short, 40)
    [System.IO.File]::WriteAllBytes($copy, $short)
    $threw = $false
    try { Test-VaultBackup -Path $copy -Passphrase $pass | Out-Null } catch { $threw = $true }
    Assert-True $threw 'a truncated container was accepted'
}

Check 'a file that is not a container at all is refused' {
    $copy = Join-Path $dest 'not-a-backup.enc'
    [System.IO.File]::WriteAllBytes($copy, [byte[]]::new(200))
    $threw = $false
    try { Test-VaultBackup -Path $copy -Passphrase $pass | Out-Null } catch { $threw = $true }
    Assert-True $threw 'a foreign file was accepted'
}

Check 'restore refuses to overwrite a record that is already there' {
    $threw = $false
    try { Restore-VaultBackup -Path $script:result.Path -Passphrase $pass | Out-Null } catch { $threw = $true }
    Assert-True $threw 'restore overwrote a live record without -Force'
}

Check 'the backup restores with the original record deleted' {
    Remove-Item -LiteralPath $script:RecordFile -Force
    Remove-Item -LiteralPath (Join-Path $env:HEALTH_VAULT_ROOT 'records\emergency-card.md') -Force
    $info = Restore-VaultBackup -Path $script:result.Path -Passphrase $pass
    $back = Get-VaultRecord
    Assert-True ($back['people']['adult-a']['conditions'][0]['name'] -eq $marker) 'the restored record lost its content'
    Assert-True (Test-Path -LiteralPath (Join-Path $env:HEALTH_VAULT_ROOT 'records\emergency-card.md')) 'a backed-up file was not restored'
    Assert-True ($info.People -eq 1) "restored people count wrong: $($info.People)"
    Assert-True ($info.Files -eq 2) "restored file count wrong: $($info.Files)"
}

Check 'force overwrites deliberately' {
    $info = Restore-VaultBackup -Path $script:result.Path -Passphrase $pass -Force
    Assert-True ($info.People -eq 1) 'forced restore reported the wrong people count'
}

Check 'a short passphrase is refused' {
    $threw = $false
    try { Export-VaultBackup -Destination $dest -Passphrase 'abc' | Out-Null } catch { $threw = $true }
    Assert-True $threw 'a three-character passphrase was accepted'
}

Check 'a container path that would escape the vault is not written' {
    $escaped = Join-Path $env:TEMP 'hv-escaped-marker.txt'
    Remove-Item -LiteralPath $escaped -Force -ErrorAction SilentlyContinue
    $payload = [ordered]@{
        format = 'health-vault-backup'; version = 1; created_at = '2026-09-18T00:00:00'
        schema = 3; people = 1
        record = $sample
        files  = [ordered]@{ '../hv-escaped-marker.txt' = 'should not be written' }
    }
    $json = $payload | ConvertTo-Json -Depth 12
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    $container = Protect-BackupBytes -Plaintext $bytes -Passphrase $pass
    [Array]::Clear($bytes, 0, $bytes.Length)
    $hostile = Join-Path $dest 'hostile.enc'
    [System.IO.File]::WriteAllBytes($hostile, $container)
    $info = Restore-VaultBackup -Path $hostile -Passphrase $pass -Force -NoFiles
    Assert-True ($info.People -eq 1) 'the hostile container did not restore its record'
    $info2 = Restore-VaultBackup -Path $hostile -Passphrase $pass -Force
    Assert-True (-not (Test-Path -LiteralPath $escaped)) 'a container wrote a file outside the vault'
    Assert-True ($info2.Files -eq 0) "the escaping path was counted as restored: $($info2.Files)"
}

Check 'a missing boundary file refuses' {
    $saved = $script:BoundaryFile
    $script:BoundaryFile = Join-Path $env:TEMP 'hv-no-such-boundary.md'
    try {
        try { Export-VaultBackup -Destination $dest -Passphrase $pass | Out-Null; throw 'expected a refusal, got a result' }
        catch { Assert-True ($_.Exception.Message -like 'REFUSING*') "wrong error: $($_.Exception.Message)" }
    } finally { $script:BoundaryFile = $saved }
}

Remove-Item -LiteralPath $env:HEALTH_VAULT_ROOT -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $dest -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures -gt 0) { Write-Host "`n$($script:Failures) check(s) failed"; exit 1 }
Write-Host "`nall backup checks passed"; exit 0
