[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$LibreOfficeSource,

    [string]$OutputDirectory,

    [string]$PythonExecutable,

    [string]$Version,

    [switch]$SkipArchive
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$libreOfficeSourcePath = (Resolve-Path -LiteralPath $LibreOfficeSource).Path
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

if (-not $PythonExecutable) {
    $virtualenvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $virtualenvPython -PathType Leaf) {
        $PythonExecutable = $virtualenvPython
    } else {
        $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if (-not $pythonCommand) {
            $pythonCommand = Get-Command python -ErrorAction SilentlyContinue |
                Select-Object -First 1
        }
        if ($pythonCommand) {
            $PythonExecutable = $pythonCommand.Source
        }
    }
}
if (-not $PythonExecutable -or -not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
    throw "Python tidak ditemukan. Buat .venv atau pasang Python 3.12+ pada PATH sebelum build."
}

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $projectRoot "dist\portable-$timestamp"
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $OutputDirectory) {
    throw "Folder output sudah ada; pilih nama folder output baru agar hasil lama tidak tertimpa: $OutputDirectory"
}

$loExecutable = $null
$loIsInstaller = (Test-Path -LiteralPath $libreOfficeSourcePath -PathType Leaf) -and
    ([System.IO.Path]::GetExtension($libreOfficeSourcePath) -ieq ".msi")
if ($loIsInstaller) {
    $signature = Get-AuthenticodeSignature -FilePath $libreOfficeSourcePath
    if ($signature.Status -ne "Valid" -or $signature.SignerCertificate.Subject -notmatch "Document Foundation") {
        throw "MSI LibreOffice harus memiliki tanda tangan Authenticode valid dari The Document Foundation."
    }
} elseif (Test-Path -LiteralPath $libreOfficeSourcePath -PathType Container) {
    foreach ($name in @("soffice.exe", "soffice.com")) {
        $candidate = Join-Path $libreOfficeSourcePath "program\$name"
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $loExecutable = $candidate
            break
        }
    }
    if (-not $loExecutable) {
        throw "Pilih folder distribusi LibreOffice lengkap yang berisi program\soffice.exe atau soffice.com."
    }
} else {
    throw "Sumber LibreOffice harus berupa folder distribusi lengkap atau installer .msi yang valid."
}

$workDirectory = Join-Path $projectRoot "build\pyinstaller-$timestamp"
New-Item -ItemType Directory -Path $workDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

& $PythonExecutable -m PyInstaller --version *> $null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller belum terpasang. Jalankan: .\.venv\Scripts\python.exe -m pip install -e '.[packaging]'"
}

if ($Version) { $env:DOCUCONVERT_BUILD_VERSION = $Version }
& $PythonExecutable -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath $OutputDirectory `
    --workpath $workDirectory `
    (Join-Path $projectRoot "DocuConvert.spec")
if ($LASTEXITCODE -ne 0) {
    throw "Build executable DocuConvert gagal (exit code $LASTEXITCODE)."
}

# PyInstaller leaves an incomplete staging EXE in the work directory. It excludes
# collected DLLs by design, so mark it non-executable to avoid confusing it with the release.
$intermediateExecutable = Join-Path $workDirectory "DocuConvert\DocuConvert.exe"
if (Test-Path -LiteralPath $intermediateExecutable -PathType Leaf) {
    Rename-Item -LiteralPath $intermediateExecutable -NewName "DocuConvert-build-only"
}

$bundleRoot = Join-Path $OutputDirectory "DocuConvert"
$libreOfficeTarget = Join-Path $bundleRoot "tools\LibreOffice"
New-Item -ItemType Directory -Path $libreOfficeTarget -Force | Out-Null

if ($loIsInstaller) {
    $msiArguments = @(
        "/a",
        "`"$libreOfficeSourcePath`"",
        "/qn",
        "TARGETDIR=`"$libreOfficeTarget`""
    )
    $extract = Start-Process `
        -FilePath (Join-Path $env:SystemRoot "System32\msiexec.exe") `
        -ArgumentList $msiArguments `
        -Wait `
        -PassThru `
        -WindowStyle Hidden
    if ($extract.ExitCode -ne 0) {
        throw "Ekstraksi administrative MSI LibreOffice gagal (exit code $($extract.ExitCode))."
    }
} else {
    Get-ChildItem -LiteralPath $libreOfficeSourcePath -Force |
        Where-Object { $_.Extension -ine ".msi" } |
        ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $libreOfficeTarget -Recurse
        }
}

$bundledSoffice = @(
    (Join-Path $libreOfficeTarget "program\soffice.exe"),
    (Join-Path $libreOfficeTarget "program\soffice.com")
) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $bundledSoffice) {
    throw "LibreOffice gagal dipaketkan; executable soffice tidak ditemukan di $libreOfficeTarget."
}

# Diet bundle: pangkas data LibreOffice yang tidak dipakai konversi headless
# (kamus, bantuan, tema ikon non-default, bahasa non-ID/EN). Menghemat ~800 MB.
$pruneScript = Join-Path $PSScriptRoot "prune_libreoffice.py"
& $PythonExecutable $pruneScript $libreOfficeTarget
if ($LASTEXITCODE -ne 0) {
    throw "Pruning LibreOffice gagal (exit code $LASTEXITCODE)."
}

$notices = Join-Path $bundleRoot "THIRD_PARTY_NOTICES.md"
Copy-Item -LiteralPath (Join-Path $projectRoot "THIRD_PARTY_NOTICES.md") -Destination $notices
Copy-Item -LiteralPath (Join-Path $projectRoot "LICENSE") -Destination (Join-Path $bundleRoot "LICENSE")
@"
DocuConvert Portable

Jalankan DocuConvert\DocuConvert.exe. Semua komponen DocuConvert sudah disertakan.
Tidak perlu memasang komponen konversi terpisah pada perangkat Windows x64.
Jangan pindahkan DocuConvert.exe keluar dari folder distribusinya.
"@ | Set-Content -LiteralPath (Join-Path $OutputDirectory "README-PORTABLE.txt") -Encoding UTF8

Write-Host "Paket portable berhasil dibuat: $bundleRoot"
if (-not $SkipArchive) {
    $archiveName = if ($Version) { "DocuConvert-Portable-$Version-Windows-x64.zip" } else { "DocuConvert-Portable-Windows-x64.zip" }
    $archivePath = Join-Path (Split-Path $OutputDirectory -Parent) $archiveName
    & $PythonExecutable (Join-Path $PSScriptRoot "package_portable.py") $OutputDirectory $archivePath
    if ($LASTEXITCODE -ne 0) { throw "Pembuatan paket ZIP DocuConvert gagal." }
}
