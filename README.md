# DocuConvert

DocuConvert adalah aplikasi desktop untuk mengonversi dan mengelola dokumen secara lokal. File yang dipilih diproses di komputer pengguna; aplikasi tidak mengunggah dokumen ke layanan cloud.

## Untuk pengguna Windows

Paket portable Windows x64 menyertakan aplikasi dan LibreOffice. Pengguna tidak perlu memasang Python atau LibreOffice secara terpisah.

1. Salin seluruh folder paket `portable-<timestamp>` yang diberikan. Jika paket dikirim sebagai ZIP, ekstrak ZIP tersebut terlebih dahulu.
2. Jangan pisahkan folder `DocuConvert` dari folder paketnya.
3. Jalankan `DocuConvert\DocuConvert.exe`.

Jangan jalankan executable staging yang berada di folder `build`; gunakan executable di folder distribusi `dist`. Pertahankan `DocuConvert\tools\LibreOffice` agar konversi Word, Excel, dan PowerPoint tetap berfungsi. Build saat ini hanya tersedia untuk Windows x64; macOS dan Linux belum didukung.

## Fitur

- Word, Excel, dan PowerPoint ke PDF.
- PDF ke Word atau gambar, dan gambar ke PDF.
- Gabungkan, pisahkan, kompres, putar, dan hapus halaman PDF.
- Tambahkan watermark dan proteksi password pada PDF.
- Riwayat lokal, pembatalan proses, pemilihan folder hasil, dan tema terang/gelap.

Konversi dokumen Office memakai LibreOffice. Paket portable sudah menyertakannya; saat menjalankan dari source, instalasi LibreOffice perlu tersedia di komputer.

## Menjalankan dari source

Memerlukan Python 3.12 atau lebih baru. Dari PowerShell di folder proyek:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m app.main
```

Untuk konversi Word/Excel/PowerPoint dari source, pasang LibreOffice Desktop atau sediakan distribusi LibreOffice lengkap pada `tools\LibreOffice`.

## Membuat paket portable Windows

Di mesin build Windows x64, siapkan environment proyek dan distribusi LibreOffice lengkap atau MSI resmi:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[packaging]"
.\scripts\build_portable.ps1 -LibreOfficeSource "D:\tools\LibreOffice"
```

Skrip menghasilkan folder baru `dist\portable-<timestamp>\`. Distribusikan seluruh folder tersebut, bukan hanya file `.exe`. Cara memakai sumber LibreOffice MSI, catatan lisensi, dan pemeriksaan rilis dijelaskan di [`docs/portable-build.md`](docs/portable-build.md) dan [`docs/THIRD_PARTY_NOTICES.md`](docs/THIRD_PARTY_NOTICES.md).

## Struktur proyek

- `app/ui/` — antarmuka desktop PySide6, komponen, tema, dan aset.
- `app/backend/` — domain, validasi, antrean job, dan konverter dokumen.
- `scripts/` — skrip build portable Windows.
- `docs/` — dokumentasi backend dan distribusi.
- `prd.md` — product requirements document.

Lihat [`docs/backend.md`](docs/backend.md) untuk alur backend dan [`docs/portable-build.md`](docs/portable-build.md) untuk panduan distribusi.
