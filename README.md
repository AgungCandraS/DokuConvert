# DocuConvert

DocuConvert adalah aplikasi desktop untuk mengonversi dan mengelola dokumen secara lokal. File yang dipilih diproses di komputer pengguna; aplikasi tidak mengunggah dokumen ke layanan cloud.

## Mengunduh dan memasang

Untuk rilis publik, pengguna memilih installer sesuai OS dari GitHub Releases:

- Windows x64: `DocuConvert-Setup-<versi>-windows-x64.exe`.
- macOS: `DocuConvert-<versi>-macos-<arsitektur>.pkg` (arsitektur yang sesuai dengan mesin build resmi).
- Ubuntu/Debian x86_64: `DocuConvert-<versi>-linux-amd64.deb`.

Jalankan installer sesuai OS dan buka DocuConvert dari menu aplikasi. Tidak perlu memasang Python atau menjalankan terminal. Paket Office menyertakan LibreOffice di Windows/macOS; paket Debian/Ubuntu meminta sistem mengelola dependency tersebut saat instalasi. Pemrosesan dokumen dilakukan lokal setelah aplikasi terpasang.

## Fitur

- Word, Excel, dan PowerPoint ke PDF.
- PDF ke Word atau gambar, dan gambar ke PDF.
- Gabungkan, pisahkan, kompres, putar, dan hapus halaman PDF.
- Tambahkan watermark dan proteksi password pada PDF.
- Riwayat lokal, pembatalan proses, pemilihan folder hasil, dan tema terang/gelap.

Konversi dokumen Office memakai LibreOffice. Installer Windows/macOS menyertakannya; paket Debian/Ubuntu memasangnya sebagai dependency. Saat menjalankan dari source, LibreOffice perlu tersedia di komputer.

## Menjalankan dari source

Memerlukan Python 3.12 atau lebih baru. Dari PowerShell di folder proyek:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m app.main
```

Untuk konversi Word/Excel/PowerPoint dari source, pasang LibreOffice Desktop atau sediakan distribusi LibreOffice lengkap pada `tools\LibreOffice`.

## Membuat installer Windows

Di mesin build Windows x64, siapkan environment proyek, Inno Setup 6, serta distribusi LibreOffice lengkap:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[packaging]"
.\scripts\build_windows_installer.ps1 -LibreOfficeSource "$env:ProgramFiles\LibreOffice"
```

Hasil `.exe` installer dan checksum ada di folder `dist\installer-windows-<timestamp>\`. Skrip lama `build_portable.ps1` tetap tersedia untuk membuat folder portable.

## Membuat paket macOS atau Linux

Build harus dijalankan pada OS target. macOS membutuhkan Python 3.12+, PyInstaller, Xcode Command Line Tools, dan LibreOffice.app:

```bash
python3 -m pip install -e '.[packaging]'
brew install --cask libreoffice
python3 scripts/build_macos_pkg.py --libreoffice-app /Applications/LibreOffice.app
```

Ubuntu 22.04+ x86_64 membutuhkan paket dependency Qt dan `dpkg-deb`:

```bash
sudo apt install dpkg-dev libreoffice libgl1 libglib2.0-0 libxcb-cursor0 libxkbcommon-x11-0
python3 -m pip install -e '.[packaging]'
python3 scripts/build_linux_deb.py
```

## Rilis lintas platform

Workflow [Build desktop installers](.github/workflows/installers.yml) membangun installer secara native pada Windows, macOS, dan Ubuntu. Jalankan manual untuk memperoleh artifact pengujian, atau push tag versi seperti `v0.1.0` untuk membuat GitHub Release berisi installer dan checksum.

Build macOS saat ini belum ditandatangani/notarized secara default. Distribusi publik yang mulus memerlukan sertifikat dan proses signing/notarization Apple; build Windows juga belum memakai code-signing certificate.

## Struktur proyek

- `app/ui/` — antarmuka desktop PySide6, komponen, tema, dan aset.
- `app/backend/` — domain, validasi, antrean job, dan konverter dokumen.
- `scripts/` — skrip build portable dan installer per OS.
- `packaging/` — konfigurasi installer Windows.
- `docs/` — dokumentasi backend dan distribusi.
- `prd.md` — product requirements document.

Lihat [`docs/backend.md`](docs/backend.md) untuk alur backend, [`docs/release-build.md`](docs/release-build.md) untuk pipeline installer lintas platform, dan [`docs/portable-build.md`](docs/portable-build.md) untuk paket portable Windows.
