# Installer lintas platform

Workflow [`installers.yml`](../.github/workflows/installers.yml) membuat artifact dari runner native. Tag `v*` menghasilkan GitHub Release berisi installer dan checksum; workflow dispatch hanya menyimpan artifact untuk diuji.

| Platform rilis saat ini | Artifact | Dependency Office |
|---|---|---|
| Windows x64 | `DocuConvert-Setup-<versi>-windows-x64.exe` | LibreOffice ikut di dalam installer |
| macOS Intel dan Apple Silicon | `DocuConvert-<versi>-macos-<arsitektur>.pkg` | LibreOffice ikut di dalam aplikasi |
| Ubuntu 22.04+ / Debian 12+ x86_64 | `DocuConvert-<versi>-linux-amd64.deb` | Dependency `libreoffice` dipasang otomatis oleh package manager |

Semua build PyInstaller harus dijalankan pada OS target. `.exe`, `.pkg`, dan `.deb` adalah artifact berbeda, bukan satu executable universal.

## Build lokal

Pasang dependency Python proyek dan packaging extra pada mesin build target:

```bash
python -m pip install -e '.[packaging]'
```

Di Windows, sediakan Inno Setup 6 dan direktori distribusi LibreOffice lengkap:

```powershell
.\scripts\build_windows_installer.ps1 `
  -LibreOfficeSource "$env:ProgramFiles\LibreOffice" `
  -Version "0.1.0"
```

Di macOS, sediakan `LibreOffice.app` untuk arsitektur mesin build:

```bash
python scripts/build_macos_pkg.py \
  --libreoffice-app /Applications/LibreOffice.app \
  --version 0.1.0
```

Di Ubuntu 22.04+ x86_64, sediakan `dpkg-deb` dan dependency runtime yang dipakai PySide6:

```bash
sudo apt install dpkg-dev libreoffice libgl1 libglib2.0-0 libxcb-cursor0 libxkbcommon-x11-0
python scripts/build_linux_deb.py --version 0.1.0
```

Setiap skrip menolak menimpa folder output yang sudah ada. Artifact diberi file `SHA256SUMS.txt`.

## Signing dan rilis publik

Installer Windows dan paket macOS saat ini dibangun tanpa code-signing identity. Akibatnya, OS dapat menampilkan peringatan publisher saat pengguna mengunduhnya. Build macOS belum dinotariskan. Sebelum distribusi publik yang mulus, siapkan sertifikat Windows dan Apple Developer ID, lakukan signing aplikasi serta installer, dan notarize aplikasi macOS. Tidak ada credential signing yang disimpan di repository.

LibreOffice didistribusikan bersama paket Windows/macOS atau dideklarasikan sebagai dependency paket Debian/Ubuntu. Lisensi dan notice dependency yang dibundel harus ditinjau serta disertakan bersama artifact rilis; lihat [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Smoke check release

Uji setiap artifact pada mesin/VM bersih dengan OS dan arsitektur yang sesuai:

1. Pasang paket dan buka DocuConvert dari shortcut/menu aplikasi.
2. Pastikan status LibreOffice tersedia pada Windows/macOS; pada Debian/Ubuntu pastikan dependency otomatis terpasang.
3. Jalankan satu konversi Office dan satu operasi PDF, lalu verifikasi hasil dapat dibuka.
4. Pastikan proses tetap berjalan tanpa koneksi internet setelah instalasi.
5. Uninstall aplikasi dan pastikan dokumen input/output pengguna tidak terhapus.

Workflow CI menguji instalasi/jalankan/uninstall Windows, instalasi dan startup macOS, serta install/start/remove paket Debian. Uji konversi dokumen dengan fixture, upgrade versi, validasi mesin bersih untuk seluruh OS, dan code signing/notarization masih perlu dilakukan sebelum rilis stabil.
