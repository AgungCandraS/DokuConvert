[CmdletBinding()]
param(
    [string]$LibreOfficeSource,

    [string]$Version = "0.1.1",

    [string]$OutputDirectory,

    [string]$PayloadDirectory,

    [string]$CompilerExecutable,

    [int]$MaxInstallerSizeMB = 500
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$distRoot = Join-Path $projectRoot "dist"
$stageDirectory = Join-Path $distRoot "installer-stage-$timestamp"

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $distRoot "installer-windows-$timestamp"
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $OutputDirectory) {
    throw "Folder output sudah ada; pilih folder baru agar installer lama tidak tertimpa: $OutputDirectory"
}
if ($MaxInstallerSizeMB -le 0) { throw "Batas ukuran installer harus lebih besar dari nol." }

$compilerCandidates = @(
    $CompilerExecutable,
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe")
) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
if (-not $compilerCandidates) {
    throw "Compiler installer tidak ditemukan. Pasang Inno Setup atau isi -CompilerExecutable."
}

if ($PayloadDirectory) {
    $PayloadDirectory = (Resolve-Path -LiteralPath $PayloadDirectory).Path
    $versionStamp = Join-Path $PayloadDirectory "_internal\app\VERSION"
    if (-not (Test-Path -LiteralPath (Join-Path $PayloadDirectory "DocuConvert.exe") -PathType Leaf)) {
        throw "Payload tidak berisi DocuConvert.exe."
    }
    if (-not (Test-Path -LiteralPath $versionStamp) -or
        (Get-Content -LiteralPath $versionStamp -Raw).Trim() -ne $Version) {
        throw "Versi payload tidak sama dengan versi installer $Version."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $PayloadDirectory "tools\LibreOffice\program\soffice.exe"))) {
        throw "Payload tidak berisi komponen konversi Office lengkap."
    }
} else {
    if (-not $LibreOfficeSource) { throw "Isi -LibreOfficeSource atau -PayloadDirectory." }
    $portableBuilder = Join-Path $PSScriptRoot "build_portable.ps1"
    $portableArguments = @{
        LibreOfficeSource = $LibreOfficeSource
        OutputDirectory = $stageDirectory
        Version = $Version
        SkipArchive = $true
    }
    & $portableBuilder @portableArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Build payload Windows gagal (exit code $LASTEXITCODE)."
    }
    $PayloadDirectory = Join-Path $stageDirectory "DocuConvert"
}

$installerScript = Join-Path $projectRoot "packaging\windows\DocuConvert.iss"
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$compilerArguments = @(
    "/Qp",
    "/DAppVersion=$Version",
    "/DPayloadDir=$PayloadDirectory",
    "/DOutputDir=$OutputDirectory",
    "/DProjectRoot=$projectRoot",
    $installerScript
)
Push-Location $projectRoot
try {
    & @($compilerCandidates)[0] @compilerArguments
} finally {
    Pop-Location
}
if ($LASTEXITCODE -ne 0) {
    throw "Kompilasi installer Inno Setup gagal (exit code $LASTEXITCODE)."
}

$installer = Get-ChildItem -LiteralPath $OutputDirectory -Filter "DocuConvert-Setup-*.exe" -File |
    Select-Object -First 1
if (-not $installer) {
    throw "Compiler selesai tanpa menghasilkan installer Windows."
}
$installerSizeMB = $installer.Length / 1000000
Write-Host ("Ukuran installer DocuConvert: {0:N1} MB" -f $installerSizeMB)
if ($installer.Length -ge ($MaxInstallerSizeMB * 1000000L)) {
    throw "Installer belum memenuhi target di bawah $MaxInstallerSizeMB MB. Hasil dipertahankan untuk diperiksa."
}
Get-FileHash -LiteralPath $installer.FullName -Algorithm SHA256 |
    ForEach-Object { "$($_.Hash.ToLowerInvariant())  $($installer.Name)" } |
    Set-Content -LiteralPath (Join-Path $OutputDirectory "SHA256SUMS.txt") -Encoding ASCII

Write-Host "Installer Windows berhasil dibuat: $($installer.FullName)"
