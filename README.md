# DocuConvert

DocuConvert adalah aplikasi desktop untuk mengonversi dan mengelola dokumen. Setelah dipasang, aplikasi berjalan di komputer pengguna dan file diproses secara lokal—tidak diunggah ke layanan cloud.

## Pasang dan mulai gunakan

1. Buka [GitHub Releases](https://github.com/AgungCandraS/DokuConvert/releases) dan unduh installer untuk sistem operasi Anda.
2. Jalankan installer dan ikuti petunjuk di layar.
3. Buka DocuConvert dari Start Menu, Applications/Launchpad, atau menu aplikasi Linux.
4. Pilih alat, klik **Tambah file**, atur opsi dan folder penyimpanan, lalu klik **Mulai proses**.
5. Setelah selesai, klik **Buka file hasil** atau buka kembali hasilnya dari halaman riwayat.

Pilih paket yang sesuai:

| Sistem operasi | Paket | Catatan |
| --- | --- | --- |
| Windows x64 | `DocuConvert-Setup-<versi>-windows-x64.exe` | LibreOffice disertakan untuk konversi Office. |
| macOS Intel / Apple Silicon | `DocuConvert-<versi>-macos-<arsitektur>.pkg` | Pilih paket sesuai arsitektur Mac. LibreOffice disertakan. |
| Ubuntu 22.04+ / Debian 12+, x86_64 | `DocuConvert-<versi>-linux-amd64.deb` | LibreOffice dipasang otomatis sebagai dependency paket. |

### Langkah instalasi

- **Windows:** buka file `.exe`, ikuti installer, lalu jalankan DocuConvert dari Start Menu. Shortcut Desktop dapat dipilih saat instalasi.
- **macOS:** buka file `.pkg`, ikuti Installer, lalu jalankan DocuConvert dari Applications atau Launchpad.
- **Ubuntu/Debian:** buka file `.deb` dengan aplikasi Software/App Center, pilih **Install**, lalu jalankan DocuConvert dari menu aplikasi.

Sesudah aplikasi terbuka, pilih alat konversi atau PDF, tambahkan file, atur pilihan yang tersedia, pilih lokasi hasil bila perlu, lalu tekan **Mulai proses**. File hasil dapat dibuka langsung dari layar selesai atau dari riwayat.

Jika halaman Releases belum berisi installer, berarti rilis paket belum dipublikasikan. Setiap push dan pull request menjalankan build CI dan menyimpan artifact uji; maintainer menerbitkan installer untuk pengguna melalui GitHub Release bertag versi. Build publik saat ini belum ditandatangani/notarized, sehingga Windows atau macOS mungkin menampilkan peringatan keamanan.

Pengguna tidak perlu memasang Python, LibreOffice secara terpisah, menjalankan Docker, membuka terminal, atau membangun aplikasi dari source. Di Windows/macOS, installer membawa LibreOffice; paket Ubuntu/Debian memasangnya sebagai dependency.

## Fitur

- Word, Excel, dan PowerPoint ke PDF.
- PDF ke Word atau gambar, serta gambar ke PDF.
- Gabungkan, pisahkan, kompres, putar, hapus halaman PDF.
- Tambahkan watermark dan proteksi password pada PDF.
- Riwayat lokal, pembatalan job, pemilihan folder hasil, serta tema terang/gelap.

Konversi PDF ke Word menggunakan `pdf2docx`; PDF hasil scan tidak menjalani OCR dan tata letak kompleks dapat berubah. Operasi PDF yang membaca dokumen terlindungi menerima password sumber; password proteksi tidak disimpan ke log atau riwayat. Hasil dipublikasikan dengan nama unik agar file sumber maupun hasil sebelumnya tidak tertimpa.

## Informasi maintainer/developer

Bagian berikut menjelaskan arsitektur dan pemeliharaan proyek; pengguna aplikasi yang hanya ingin memasang dan mengonversi dokumen tidak perlu mengikuti langkah build manual.

## Struktur proyek

```text
app/
├── backend/                 # domain, job, validasi, konversi, dan akses filesystem
│   ├── application/         # orchestration job dan layanan konversi
│   ├── converters/          # implementasi operasi format dokumen
│   ├── domain/              # model, enum, dan error domain
│   └── infrastructure/      # LibreOffice, filesystem, settings, logging, history
├── ui/                      # antarmuka desktop PySide6
│   ├── components/          # widget yang dapat digunakan ulang
│   ├── controllers/         # adapter antara event UI dan backend
│   └── resources/           # ikon dan aset UI
├── main.py                  # entry point aplikasi
└── backend/bootstrap.py     # komposisi dependency dan runtime backend
packaging/windows/           # konfigurasi Inno Setup
scripts/                     # build paket dan smoke test
.github/workflows/           # build native dan publikasi GitHub Release
docker/linux-smoke/          # container Ubuntu untuk uji install/start paket Linux di CI
prd.md                       # kebutuhan produk
README.md                    # dokumentasi utama proyek
LICENSE                      # lisensi MIT untuk kode proyek
THIRD_PARTY_NOTICES.md       # pemberitahuan lisensi dependency dan aset
```

`app/backend` dan `app/ui` adalah package saudara di bawah `app`, bukan kode yang tercampur. Ini wajar untuk aplikasi desktop Python: `ui` adalah lapisan presentasi, bukan frontend web. UI memanggil backend melalui `ui/controllers` dan `ui/dependencies`; backend tidak bergantung pada PySide6. Pertahankan batas ini saat menambah fitur. Memindahkan atau mengganti nama package `ui` menjadi `frontend` tidak memberi pemisahan runtime tambahan dan hanya menambah perubahan import.

## Backend dan alur job

`app/backend/bootstrap.py:create_backend()` membuat runtime layanan: registry converter, validasi, history, dan `JobManager`. UI mengubah isian form menjadi `ConversionJob`, lalu `JobManager` memprosesnya di worker thread agar UI tetap responsif. Event job (`queued`, `running`, `completed`, `failed`, `cancelled`) diteruskan kembali ke UI; callback yang mengubah widget harus dijalankan di main thread Qt.

Backend dapat dipakai tanpa UI desktop:

```python
from pathlib import Path

from app.backend import ConversionJob, OperationType, create_backend

runtime = create_backend()
unsubscribe = runtime.jobs.subscribe(
    lambda event: print(event.job_id, event.status, event.progress, event.message)
)
job = ConversionJob(
    operation=OperationType.MERGE_PDF,
    source_files=[Path("bagian-1.pdf"), Path("bagian-2.pdf")],
    output_directory=Path("hasil"),
)
runtime.jobs.submit(job)
# Simpan job.id jika perlu membatalkan: runtime.jobs.cancel(job.id)
runtime.close(wait_for_jobs=True)
unsubscribe()
```

`submit()` memasukkan job ke antrean; validasi berjalan di worker. Operasi menerima key katalog UI seperti `word_to_pdf`, `excel_to_pdf`, `powerpoint_to_pdf`, `pdf_to_word`, `image_to_pdf`, `pdf_to_image`, `merge_pdf`, `split_pdf`, `compress_pdf`, `rotate_pdf`, `delete_pages`, `watermark_pdf`, dan `protect_pdf`. Opsi operasi ditentukan oleh converter dan form alat terkait. Job memakai staging sementara di folder hasil dan menerbitkan output secara atomik; file sementara dibersihkan setelah berhasil, gagal, atau dibatalkan.

### LibreOffice

LibreOffice diperlukan untuk konversi Word/Excel/PowerPoint dan ODT ke PDF. Aplikasi mencari executable melalui pengaturan pengguna, `DOCUCONVERT_LIBREOFFICE_PATH`, folder LibreOffice di samping aplikasi, lalu `PATH` dan lokasi instalasi OS. Distribusi Windows/macOS membawa LibreOffice lengkap; paket Debian/Ubuntu mendeklarasikannya sebagai dependency. Saat menjalankan dari source, pasang LibreOffice Desktop atau siapkan distribusi lengkap—`soffice` saja tidak cukup.

## Menjalankan dari source

Memerlukan Python 3.12 atau lebih baru. Dari PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m app.main
```

Di macOS/Linux, aktivasi environment dengan `source .venv/bin/activate`. Instalasi development memuat `pytest` dan Ruff. Jalankan pemeriksaan dengan:

```bash
python -m compileall -q app scripts
python -m pytest
ruff check app scripts
```

Konversi Office saat development membutuhkan LibreOffice yang dapat ditemukan backend. PySide6, PyMuPDF, Pillow, dan pdf2docx dipasang dari dependency `pyproject.toml`.

## Build paket lokal

Setiap installer harus dibangun pada OS target menggunakan Python 3.12+; build PyInstaller bukan satu executable universal lintas OS. Pasang extra packaging terlebih dahulu:

```bash
python -m pip install -e '.[packaging]'
```

### Windows x64 installer

Butuh Inno Setup 6 dan distribusi LibreOffice lengkap (folder hasil ekstrak atau MSI resmi):

```powershell
.\scripts\build_windows_installer.ps1 `
  -LibreOfficeSource "$env:ProgramFiles\LibreOffice" `
  -Version "0.1.0"
```

Skrip membuat payload PyInstaller, menyalin LibreOffice, lalu menjalankan Inno Setup. Installer dan checksum ada di `dist/installer-windows-<timestamp>/`. Untuk membuat folder portable Windows tanpa installer, gunakan `scripts/build_portable.ps1`; bagikan seluruh folder output, bukan hanya `DocuConvert.exe`.

### macOS installer

Butuh Xcode Command Line Tools dan `LibreOffice.app` yang arsitekturnya sesuai mesin build:

```bash
brew install --cask libreoffice
python scripts/build_macos_pkg.py \
  --libreoffice-app /Applications/LibreOffice.app \
  --version 0.1.0
```

Skrip membuat `.pkg` yang memasang `DocuConvert.app` ke `/Applications`.

### Debian/Ubuntu installer

Target saat ini Ubuntu 22.04+ atau Debian 12+, x86_64. Mesin build membutuhkan `dpkg-deb` dan dependency Qt sistem:

```bash
sudo apt install dpkg-dev libreoffice libgl1 libglib2.0-0 libxcb-cursor0 libxkbcommon-x11-0
python scripts/build_linux_deb.py --version 0.1.0
```

Paket `.deb` mencantumkan LibreOffice dan library sistem sebagai dependency agar package manager memasangnya.

Skrip build menolak menimpa folder output yang sudah ada dan membuat `SHA256SUMS.txt` di samping installer.

## Build dan rilis melalui GitHub Actions

Workflow [Build desktop installers](.github/workflows/installers.yml) membangun paket secara native di runner Windows, macOS Intel, macOS Apple Silicon, dan Ubuntu. Workflow berjalan otomatis pada setiap push dan pull request, serta dapat dijalankan manual. Setiap job memasang paket lalu menjalankan smoke test; artifact berisi installer dan checksum.

- **Uji build otomatis:** setiap push dan pull request memulai build. Hasilnya tersedia sebagai workflow artifacts, bukan GitHub Release.
- **Uji manual:** buka tab **Actions**, pilih **Build installers**, lalu **Run workflow**.
- **Rilis:** setelah hasil uji ditinjau, push tag versi seperti `v0.1.0`. Workflow tag akan membangun ulang semua paket dan membuat GitHub Release.
- **Unduhan pengguna:** bagikan halaman Releases; pengguna memilih file berdasarkan OS dan arsitektur.

### Hasil validasi installer

Workflow [run #36604467749](https://github.com/AgungCandraS/DokuConvert/actions/runs/36604467749) lulus pada 29 September 2026 (UTC) untuk Windows x64, macOS Intel, macOS Apple Silicon, dan Ubuntu 22.04 amd64. Smoke test Windows memasang installer ke lokasi default, membuka aplikasi, lalu menghapusnya; smoke test macOS memasang paket dan memeriksa startup aplikasi; smoke test Linux memasang `.deb` pada image Ubuntu bersih, memeriksa startup, lalu menghapus paket. Installer dan checksum tersedia sebagai artifact pada run tersebut—belum sebagai GitHub Release.

Workflow tidak mengubah satu build menjadi paket lintas OS. Signing juga belum dikonfigurasi: rilis Windows memerlukan code-signing certificate, sedangkan macOS perlu Developer ID signing dan notarization agar peringatan OS berkurang. Rahasia signing harus ditambahkan sebagai GitHub Actions secrets; jangan commit credential ke repository.

Docker hanya dipakai job Linux untuk memasang dan menjalankan `.deb` di image Ubuntu 22.04 bersih tanpa akses jaringan saat smoke test. Docker bukan cara menjalankan GUI desktop untuk pengguna dan tidak menggantikan runner macOS/Windows.

### Acceptance sebelum rilis stabil

1. Pastikan semua job workflow lulus dan checksum tersedia.
2. Uji installer di VM bersih untuk tiap OS/arsitektur yang dirilis.
3. Pasang, buka aplikasi, konversi minimal satu dokumen Office dan satu operasi PDF, lalu uninstall.
4. Pastikan dokumen input/output pengguna tetap ada setelah uninstall.
5. Lengkapi signing/notarization dan tinjau kewajiban distribusi dependency.

CI saat ini memverifikasi build, instalasi, startup aplikasi, serta uninstall pada target yang relevan; CI belum menjalankan pengujian konversi dengan fixture pada semua OS. Untuk rilis stabil, tetap lakukan acceptance test konversi dan data pengguna pada VM bersih.

## Lisensi dan pemberitahuan pihak ketiga

Kode DocuConvert dilisensikan di bawah [MIT License](LICENSE). Lisensi ini mengizinkan penggunaan, modifikasi, dan redistribusi dengan menyertakan copyright dan teks lisensi. Dependency, LibreOffice, dan ikon pihak ketiga tetap mengikuti lisensi masing-masing; baca [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) dan berkas lisensi upstream yang ikut pada paket. Pemberitahuan ini bukan nasihat hukum.
