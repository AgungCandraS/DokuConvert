[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$LibreOfficeSource,

    [string]$Version = "0.1.0",

    [string]$OutputDirectory
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

$portableBuilder = Join-Path $PSScriptRoot "build_portable.ps1"
$pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $pythonCommand) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
}
$portableArguments = @{
    LibreOfficeSource = $LibreOfficeSource
    OutputDirectory = $stageDirectory
}
if ($pythonCommand) {
    $portableArguments.PythonExecutable = $pythonCommand.Source
}
& $portableBuilder @portableArguments
if ($LASTEXITCODE -ne 0) {
    throw "Build payload Windows gagal (exit code $LASTEXITCODE)."
}

$compilerCandidates = @(
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
if (-not $compilerCandidates) {
    throw "Inno Setup 6 tidak ditemukan. Pasang Inno Setup 6 lalu jalankan ulang build installer."
}

$payloadDirectory = Join-Path $stageDirectory "DocuConvert"
$installerScript = Join-Path $projectRoot "packaging\windows\DocuConvert.iss"
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$compilerArguments = @(
    "/DAppVersion=$Version",
    "/DPayloadDir=$payloadDirectory",
    "/DOutputDir=$OutputDirectory",
    $installerScript
)
Push-Location $projectRoot
try {
    & $compilerCandidates[0] @compilerArguments
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
Get-FileHash -LiteralPath $installer.FullName -Algorithm SHA256 |
    ForEach-Object { "$($_.Hash.ToLowerInvariant())  $($installer.Name)" } |
    Set-Content -LiteralPath (Join-Path $OutputDirectory "SHA256SUMS.txt") -Encoding ASCII

Write-Host "Installer Windows berhasil dibuat: $($installer.FullName)"
