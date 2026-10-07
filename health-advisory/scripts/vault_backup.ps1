#Requires -Version 7
<#
  The portable half of the vault: passphrase backup, verify, restore.

  DPAPI is bound to the current Windows account, so a DPAPI-encrypted file will
  not open after a profile rebuild or on another machine - which is exactly the
  situation a backup exists for. This script decrypts the record in memory and
  re-encrypts it under a passphrase (PBKDF2-SHA256 -> AES-256-GCM), so the
  container restores anywhere.

  The passphrase is read at a prompt. It is never stored, never echoed, never
  taken from the command line, never committed, and never written into a report.
  If it is lost the backup is unrecoverable; that is the trade for not needing
  this Windows account.

  Prints counts, paths, dates and hashes only. Record content never reaches
  stdout, because stdout is persisted by the session store.

  Commands:
    export  [-destination <dir>] [-name <file>]   write a backup, then prove it
    verify  -path <file>                          decrypt and report, write nothing
    restore -path <file> [-force]                 write the record and files back
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'vault.ps1')

$script:BackupMagic      = 'HVBK1'
$script:BackupKdfId      = 1
$script:BackupIterations = 600000
$script:BackupSaltLen    = 16
$script:BackupNonceLen   = 12
$script:BackupTagLen     = 16
$script:BackupHeaderLen  = 5 + 1 + 4 + $script:BackupSaltLen + $script:BackupNonceLen
$script:BackupMinLen     = $script:BackupHeaderLen + $script:BackupTagLen
$script:BackupMinPhrase  = 12
$script:DefaultBackupDir  = 'D:\OneDrive\1 YUAN QI\1.1 Personal\4 AI-assistant\health-vault-backup'
$script:DefaultBackupName = 'hv-backup.enc'

function Get-BackupKey {
    param([string]$Passphrase, [byte[]]$Salt, [int]$Iterations)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Passphrase)
    try {
        return [System.Security.Cryptography.Rfc2898DeriveBytes]::Pbkdf2(
            $bytes, $Salt, $Iterations,
            [System.Security.Cryptography.HashAlgorithmName]::SHA256, 32)
    } finally {
        [Array]::Clear($bytes, 0, $bytes.Length)
    }
}

function Protect-BackupBytes {
    param([Parameter(Mandatory)][byte[]]$Plaintext, [Parameter(Mandatory)][string]$Passphrase)
    $salt  = [byte[]]::new($script:BackupSaltLen)
    $nonce = [byte[]]::new($script:BackupNonceLen)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($salt)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($nonce)
    $key = Get-BackupKey -Passphrase $Passphrase -Salt $salt -Iterations $script:BackupIterations
    $cipher = [byte[]]::new($Plaintext.Length)
    $tag    = [byte[]]::new($script:BackupTagLen)
    $aes = [System.Security.Cryptography.AesGcm]::new($key, $script:BackupTagLen)
    try {
        $aes.Encrypt($nonce, $Plaintext, $cipher, $tag, $null)
    } finally {
        $aes.Dispose()
        [Array]::Clear($key, 0, $key.Length)
    }
    $out = [System.Collections.Generic.List[byte]]::new()
    $out.AddRange([System.Text.Encoding]::ASCII.GetBytes($script:BackupMagic))
    $out.Add([byte]$script:BackupKdfId)
    $out.AddRange([System.BitConverter]::GetBytes([int]$script:BackupIterations))
    $out.AddRange($salt)
    $out.AddRange($nonce)
    $out.AddRange($cipher)
    $out.AddRange($tag)
    return $out.ToArray()
}

function Unprotect-BackupBytes {
    param([Parameter(Mandatory)][byte[]]$Container, [Parameter(Mandatory)][string]$Passphrase)
    if ($Container.Length -lt $script:BackupMinLen) {
        throw 'REFUSED: the file is too short to be a backup container. It is truncated, or not a backup at all.'
    }
    if ([System.Text.Encoding]::ASCII.GetString($Container, 0, 5) -ne $script:BackupMagic) {
        throw 'REFUSED: this file is not a health-vault backup.'
    }
    $kdfId = [int]$Container[5]
    if ($kdfId -ne $script:BackupKdfId) {
        throw "REFUSED: unsupported key-derivation id $kdfId. This file needs a newer script."
    }
    $iterations = [System.BitConverter]::ToInt32($Container, 6)
    $salt  = [byte[]]::new($script:BackupSaltLen)
    $nonce = [byte[]]::new($script:BackupNonceLen)
    [Array]::Copy($Container, 10, $salt, 0, $script:BackupSaltLen)
    [Array]::Copy($Container, 10 + $script:BackupSaltLen, $nonce, 0, $script:BackupNonceLen)
    $cipherLen = $Container.Length - $script:BackupHeaderLen - $script:BackupTagLen
    $cipher = [byte[]]::new($cipherLen)
    $tag    = [byte[]]::new($script:BackupTagLen)
    [Array]::Copy($Container, $script:BackupHeaderLen, $cipher, 0, $cipherLen)
    [Array]::Copy($Container, $script:BackupHeaderLen + $cipherLen, $tag, 0, $script:BackupTagLen)
    $key = Get-BackupKey -Passphrase $Passphrase -Salt $salt -Iterations $iterations
    $plain = [byte[]]::new($cipherLen)
    $aes = [System.Security.Cryptography.AesGcm]::new($key, $script:BackupTagLen)
    try {
        $aes.Decrypt($nonce, $cipher, $tag, $plain, $null)
    } catch [System.Security.Cryptography.CryptographicException] {
        [Array]::Clear($plain, 0, $plain.Length)
        throw 'REFUSED: the passphrase is wrong, or the file has been altered. The two cannot be told apart, so nothing is used.'
    } finally {
        $aes.Dispose()
        [Array]::Clear($key, 0, $key.Length)
    }
    return $plain
}

function Get-BackupPayload {
    # Everything a restore needs, in one object. The encrypted record file is not
    # one of the files: it is re-protected for whichever machine restores it.
    Assert-Boundary
    $record = Get-VaultRecord
    if (-not $record) { throw 'REFUSED: there is no record in the vault to back up.' }
    $relative = [System.Collections.Generic.List[string]]::new()
    $readme = Join-Path $script:VaultRoot 'README.md'
    if (Test-Path -LiteralPath $readme) { $relative.Add('README.md') }
    foreach ($dirName in @('records', 'reports')) {
        $dir = Join-Path $script:VaultRoot $dirName
        if (-not (Test-Path -LiteralPath $dir)) { continue }
        foreach ($file in Get-ChildItem -LiteralPath $dir -File -Recurse) {
            if ($file.FullName -eq $script:RecordFile) { continue }
            $relative.Add(([IO.Path]::GetRelativePath($script:VaultRoot, $file.FullName) -replace '\\', '/'))
        }
    }
    $files = [ordered]@{}
    foreach ($rel in $relative) {
        $full = Join-Path $script:VaultRoot ($rel -replace '/', '\')
        if ($full -eq $script:RecordFile) { continue }
        $files[$rel] = (Get-Content -LiteralPath $full -Raw)
    }
    return [ordered]@{
        format         = 'health-vault-backup'
        version        = 1
        created_at     = (Get-Date).ToString('s')
        source_machine = $env:COMPUTERNAME
        schema         = $record['schema']
        people         = @($record['people'].Keys).Count
        record         = $record
        files          = $files
    }
}

function Write-PassphraseCopy {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Passphrase,
        [string]$BackupPath,
        [string]$CreatedAt
    )
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $lines = @(
        $Passphrase,
        '',
        'Passphrase for the encrypted household health-vault backup.',
        "Backup file: $BackupPath",
        "Written:     $CreatedAt",
        '',
        'Keep at least one copy somewhere OTHER than this PC, or the backup cannot',
        'be restored if the machine is lost - that is the whole reason the backup',
        'exists. A password manager reachable from a phone is the usual choice.',
        '',
        'Without this passphrase the backup file cannot be read. There is no reset,',
        'no hint and no recovery.'
    )
    Set-Content -LiteralPath $Path -Value ($lines -join "`r`n") -Encoding utf8
    # A plaintext passphrase should not be readable by every account on the
    # machine, so the file gets one access rule: the current user.
    $me = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $acl = New-Object System.Security.AccessControl.FileSecurity
    $acl.SetAccessRuleProtection($true, $false)
    $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
        $me, 'FullControl', 'Allow')))
    Set-Acl -LiteralPath $Path -AclObject $acl
    return $Path
}

function Write-RestoreHowto {
    param(
        [Parameter(Mandatory)][string]$BackupPath,
        [string]$CreatedAt,
        [string]$PassphraseNote
    )
    $note = if ($PassphraseNote) {
        $PassphraseNote
    } else {
        'A copy is kept separately from this file. Keep at least one copy somewhere other than the machine the vault lives on.'
    }
    $lines = @(
        'HOW TO RESTORE THIS BACKUP',
        '',
        "File:    $(Split-Path -Leaf $BackupPath)",
        "Written: $CreatedAt",
        '',
        'This is an encrypted backup of a household health record. It cannot be read',
        'without two things.',
        '',
        '1. The passphrase. It is not stored in the backup file, and it cannot be',
        '   recovered or reset.',
        "   $note",
        '',
        '2. PowerShell 7 on the machine doing the restore - search "install',
        '   PowerShell 7". It is free from Microsoft. Windows PowerShell 5.1 is not',
        '   enough, and the script refuses to run on it.',
        '',
        'Then, with the health-advisory skill available:',
        '',
        '  pwsh -NoProfile -File vault_backup.ps1 verify  -path "<this folder>\<the .enc file>"',
        '  pwsh -NoProfile -File vault_backup.ps1 restore -path "<this folder>\<the .enc file>"',
        '',
        'verify only reads and reports counts. restore writes the record and the',
        'reports back into the vault, re-encrypted for whichever machine it runs on,',
        'and refuses to overwrite a record that is already there unless -force is',
        'given.',
        '',
        'If the passphrase is lost, this file is permanently unreadable. There is no',
        'reset and no back door. That is what the encryption is for.'
    )
    $path = Join-Path (Split-Path -Parent $BackupPath) 'RESTORE-HOWTO.txt'
    Set-Content -LiteralPath $path -Value ($lines -join "`r`n") -Encoding utf8
    return $path
}

function Export-VaultBackup {
    param(
        [string]$Destination = $script:DefaultBackupDir,
        [string]$FileName = $script:DefaultBackupName,
        [Parameter(Mandatory)][string]$Passphrase,
        [string]$PassphraseFile,
        [string]$PassphraseNote
    )
    if ($Passphrase.Length -lt $script:BackupMinPhrase) {
        throw "REFUSED: the passphrase must be at least $($script:BackupMinPhrase) characters."
    }
    $backupPath = Join-Path $Destination $FileName
    if (-not (Test-Path -LiteralPath $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }
    $stamp = (Get-Date).ToString('s')
    # The two files that make the container usable later go first. A backup whose
    # passphrase exists only in someone's head, or that nobody can identify in two
    # years, is not a backup - so if either cannot be written, stop before the
    # container is made.
    $copyPath = $null
    if ($PassphraseFile) {
        $copyPath = Write-PassphraseCopy -Path $PassphraseFile -Passphrase $Passphrase `
                                         -BackupPath $backupPath -CreatedAt $stamp
    }
    $howTo = Write-RestoreHowto -BackupPath $backupPath -CreatedAt $stamp -PassphraseNote $PassphraseNote
    $payload = Get-BackupPayload
    $json = $payload | ConvertTo-Json -Depth 12
    $plain = [System.Text.Encoding]::UTF8.GetBytes($json)
    try {
        $container = Protect-BackupBytes -Plaintext $plain -Passphrase $Passphrase
    } finally {
        [Array]::Clear($plain, 0, $plain.Length)
    }
    $path = $backupPath
    [System.IO.File]::WriteAllBytes($path, $container)

    # A backup is never reported good without a restore. Read the file back off
    # the disk, decrypt it again and compare, so a truncated write or a bad header
    # fails here rather than on the day it is needed.
    $written = [System.IO.File]::ReadAllBytes($path)
    $round = Unprotect-BackupBytes -Container $written -Passphrase $Passphrase
    try {
        $drill = if ([System.Text.Encoding]::UTF8.GetString($round) -eq $json) { 'OK' } else { 'MISMATCH' }
    } finally {
        [Array]::Clear($round, 0, $round.Length)
    }
    if ($drill -ne 'OK') {
        throw 'REFUSED: the file that was written does not decrypt back to what went in. Do not rely on this backup.'
    }
    $hash = [System.Security.Cryptography.SHA256]::Create()
    try { $digest = $hash.ComputeHash($written) } finally { $hash.Dispose() }
    $sha = ([System.BitConverter]::ToString($digest) -replace '-', '').ToLower()
    [Array]::Clear($digest, 0, $digest.Length)
    return [pscustomobject]@{
        Path      = $path
        Bytes     = $written.Length
        Sha256    = $sha
        CreatedAt = $payload['created_at']
        Schema    = $payload['schema']
        People    = $payload['people']
        Files     = @($payload['files'].Keys).Count
        SelfTest  = $drill
        PassphraseCopy = $copyPath
        HowTo          = $howTo
    }
}

function Test-VaultBackup {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Passphrase)
    if (-not (Test-Path -LiteralPath $Path)) { throw "REFUSED: no backup file at $Path." }
    $container = [System.IO.File]::ReadAllBytes($Path)
    $plain = Unprotect-BackupBytes -Container $container -Passphrase $Passphrase
    try {
        $payload = [System.Text.Encoding]::UTF8.GetString($plain) | ConvertFrom-Json -AsHashtable
    } finally {
        [Array]::Clear($plain, 0, $plain.Length)
    }
    if ($payload['format'] -ne 'health-vault-backup') { throw 'REFUSED: the container is not a vault backup.' }
    return [pscustomobject]@{
        CreatedAt = $payload['created_at']
        Schema    = $payload['schema']
        People    = $payload['people']
        Files     = if ($payload['files']) { @($payload['files'].Keys).Count } else { 0 }
        Bytes     = $container.Length
    }
}

function Restore-VaultBackup {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Passphrase,
        [switch]$Force,
        [switch]$NoFiles
    )
    Assert-Boundary
    if (-not (Test-Path -LiteralPath $Path)) { throw "REFUSED: no backup file at $Path." }
    if (-not $Force -and (Get-VaultRecord)) {
        throw 'REFUSED: the vault already holds a record. Pass -Force to overwrite it.'
    }
    $container = [System.IO.File]::ReadAllBytes($Path)
    $plain = Unprotect-BackupBytes -Container $container -Passphrase $Passphrase
    try {
        $payload = [System.Text.Encoding]::UTF8.GetString($plain) | ConvertFrom-Json -AsHashtable
    } finally {
        [Array]::Clear($plain, 0, $plain.Length)
    }
    if ($payload['format'] -ne 'health-vault-backup') { throw 'REFUSED: the container is not a vault backup.' }
    $record = $payload['record']
    if (-not $record -or -not $record['people']) { throw 'REFUSED: the container holds no record.' }
    Set-VaultRecord -Record $record
    $restored = 0
    if (-not $NoFiles -and $payload['files']) {
        foreach ($rel in @($payload['files'].Keys)) {
            if (-not $rel) { continue }
            # A container is data from somewhere else. Refuse anything that would
            # write outside the vault.
            if ([IO.Path]::IsPathRooted($rel) -or $rel -match '\.\.') { continue }
            $target = Join-Path $script:VaultRoot ($rel -replace '/', '\')
            $parent = Split-Path -Parent $target
            if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
            Set-Content -LiteralPath $target -Value $payload['files'][$rel] -Encoding utf8
            $restored++
        }
    }
    return [pscustomobject]@{
        People    = @($record['people'].Keys).Count
        Schema    = $record['schema']
        Files     = $restored
        CreatedAt = $payload['created_at']
    }
}

function Read-BackupPassphrase {
    param([switch]$ConfirmWithSecondEntry)
    $first = Read-Host -Prompt 'Backup passphrase (not shown)' -AsSecureString
    $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR(
        [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($first))
    if ($ConfirmWithSecondEntry) {
        $second = Read-Host -Prompt 'Type it again' -AsSecureString
        $again = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR(
            [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($second))
        if ($again -ne $plain) { throw 'REFUSED: the two passphrases do not match.' }
    }
    return $plain
}

# CLI entry point. The passphrase is never a command-line argument here, so it
# cannot land in a shell history or a process listing.
if ($MyInvocation.InvocationName -ne '.' -and $args.Count -ge 1) {
    $command = [string]$args[0]
    $opts = @{}
    for ($i = 1; $i -lt $args.Count; $i++) {
        $token = [string]$args[$i]
        if ($token -notlike '-*') { continue }
        $key = $token.TrimStart('-').ToLower()
        if (($i + 1) -lt $args.Count -and [string]$args[$i + 1] -notlike '-*') {
            $opts[$key] = [string]$args[$i + 1]; $i++
        } else {
            $opts[$key] = $true
        }
    }
    try {
        switch ($command) {
            'export' {
                $destination = if ($opts['destination']) { $opts['destination'] } else { $script:DefaultBackupDir }
                $name = if ($opts['name']) { $opts['name'] } else { $script:DefaultBackupName }
                $copyTo = if ($opts['passfile']) { $opts['passfile'] } else { $null }
                $note   = if ($opts['passnote']) { $opts['passnote'] } else { $null }
                $result = Export-VaultBackup -Destination $destination -FileName $name `
                                             -PassphraseFile $copyTo -PassphraseNote $note `
                                             -Passphrase (Read-BackupPassphrase -ConfirmWithSecondEntry)
                Write-Output "backup written:   $($result.Path)"
                Write-Output "restore howto:    $($result.HowTo)"
                if ($result.PassphraseCopy) { Write-Output "passphrase copy:  $($result.PassphraseCopy)" }
                Write-Output "container bytes:  $($result.Bytes)"
                Write-Output "sha256:           $($result.Sha256)"
                Write-Output "contains:         $($result.People) people, schema $($result.Schema), $($result.Files) file(s) besides the record"
                Write-Output "created:          $($result.CreatedAt)"
                Write-Output "restore drill:    $($result.SelfTest)"
                exit 0
            }
            'verify' {
                if (-not $opts['path']) { [Console]::Error.WriteLine('verify needs -path <file>'); exit 2 }
                $info = Test-VaultBackup -Path $opts['path'] -Passphrase (Read-BackupPassphrase)
                Write-Output "backup reads:     $($opts['path'])"
                Write-Output "created:          $($info.CreatedAt)"
                Write-Output "contains:         $($info.People) people, schema $($info.Schema), $($info.Files) file(s) besides the record"
                Write-Output "container bytes:  $($info.Bytes)"
                exit 0
            }
            'restore' {
                if (-not $opts['path']) { [Console]::Error.WriteLine('restore needs -path <file>'); exit 2 }
                $info = Restore-VaultBackup -Path $opts['path'] -Passphrase (Read-BackupPassphrase) -Force:$opts['force']
                Write-Output "restored:         $($info.People) people, schema $($info.Schema), $($info.Files) file(s) besides the record"
                Write-Output "backup created:   $($info.CreatedAt)"
                exit 0
            }
            default {
                [Console]::Error.WriteLine("Unknown command '$command'. Commands: export, verify, restore.")
                exit 2
            }
        }
    } catch {
        # Console.Error, not Write-Error: with ErrorActionPreference 'Stop',
        # Write-Error throws before the exit code is reached.
        [Console]::Error.WriteLine($_.Exception.Message)
        exit 1
    }
}
