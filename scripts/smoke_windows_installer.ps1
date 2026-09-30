[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Installer,

    [Parameter(Mandatory = $true)]
    [string]$PayloadDirectory,

    [string]$VerificationDirectory,

    [string]$PythonExecutable
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$installerPath = (Resolve-Path -LiteralPath $Installer).Path
$payloadPath = (Resolve-Path -LiteralPath $PayloadDirectory).Path
if (-not $PythonExecutable) {
    $PythonExecutable = Join-Path $projectRoot ".venv\Scripts\python.exe"
}
if (-not $VerificationDirectory) {
    $VerificationDirectory = Join-Path $projectRoot ("build\installer-verification-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
}
$VerificationDirectory = [System.IO.Path]::GetFullPath($VerificationDirectory)
$buildRoot = [System.IO.Path]::GetFullPath((Join-Path $projectRoot "build")) + [System.IO.Path]::DirectorySeparatorChar
if (-not $VerificationDirectory.StartsWith($buildRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Uji installer hanya boleh menggunakan folder baru di dalam build proyek."
}
if (Test-Path -LiteralPath $VerificationDirectory) {
    throw "Folder verifikasi sudah ada; pilih folder baru."
}
New-Item -ItemType Directory -Path $VerificationDirectory | Out-Null
$installDirectory = Join-Path $VerificationDirectory "installed"
$installLog = Join-Path $VerificationDirectory "install.log"
$installArguments = @(
    "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/VERIFY=1", "/NOICONS", "/TASKS=",
    "/DIR=`"$installDirectory`"", "/LOG=`"$installLog`""
)
Write-Host "Menguji pemasangan installer DocuConvert..."
$installation = Start-Process -FilePath $installerPath -ArgumentList $installArguments -WindowStyle Hidden -Wait -PassThru
if ($installation.ExitCode -ne 0) { throw "Pemasangan gagal; lihat $installLog" }

Write-Host "Membandingkan seluruh file instalasi dengan payload asli..."
$verifiedFiles = 0
Get-ChildItem -LiteralPath $payloadPath -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($payloadPath.Length).TrimStart('\')
    $installedFile = Join-Path $installDirectory $relative
    if (-not (Test-Path -LiteralPath $installedFile -PathType Leaf)) {
        throw "File tidak terpasang: $relative"
    }
    $originalHash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    $installedHash = (Get-FileHash -LiteralPath $installedFile -Algorithm SHA256).Hash
    if ($originalHash -ne $installedHash) { throw "Isi file berubah saat pemasangan: $relative" }
    $verifiedFiles += 1
}
Write-Host "Semua $verifiedFiles file instalasi identik dengan payload."

& $PythonExecutable (Join-Path $PSScriptRoot "smoke_frozen_app.py") (Join-Path $installDirectory "DocuConvert.exe")
if ($LASTEXITCODE -ne 0) { throw "Aplikasi hasil instalasi gagal dibuka." }
& $PythonExecutable (Join-Path $PSScriptRoot "verify_conversions.py") (Join-Path $installDirectory "tools\LibreOffice\program\soffice.exe")
if ($LASTEXITCODE -ne 0) { throw "Konversi Office hasil instalasi gagal." }

$document = Join-Path $VerificationDirectory "user-document.txt"
Set-Content -LiteralPath $document -Value "Dokumen pengguna tetap aman." -Encoding UTF8
$documentHash = (Get-FileHash -LiteralPath $document -Algorithm SHA256).Hash
$uninstallerPath = (Resolve-Path -LiteralPath (Join-Path $installDirectory "unins000.exe")).Path
if (-not $uninstallerPath.StartsWith($buildRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Lokasi uninstaller berada di luar folder uji."
}
$uninstallLog = Join-Path $VerificationDirectory "uninstall.log"
$uninstallArguments = @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/LOG=`"$uninstallLog`"")
$uninstallation = Start-Process -FilePath $uninstallerPath -ArgumentList $uninstallArguments -WindowStyle Hidden -Wait -PassThru
if ($uninstallation.ExitCode -ne 0) { throw "Uninstall paket uji gagal." }
$deadline = (Get-Date).AddSeconds(30)
while ((Test-Path -LiteralPath (Join-Path $installDirectory "DocuConvert.exe")) -and (Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 1
}
if (Test-Path -LiteralPath (Join-Path $installDirectory "DocuConvert.exe")) {
    throw "Executable masih ada setelah uninstall."
}
if ((Get-FileHash -LiteralPath $document -Algorithm SHA256).Hash -ne $documentHash) {
    throw "Dokumen pengguna berubah setelah uninstall."
}
$report = [ordered]@{
    installer = $installerPath
    sizeBytes = (Get-Item -LiteralPath $installerPath).Length
    identicalFiles = $verifiedFiles
    startup = "passed"
    officeConversions = "passed"
    uninstall = "passed"
    userDocument = "preserved"
}
$report | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $VerificationDirectory "report.json") -Encoding UTF8
Write-Host "Uji installer DocuConvert lulus. Laporan: $VerificationDirectory\report.json"
