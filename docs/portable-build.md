# Build paket Windows portable

Paket portable menyertakan executable DocuConvert dan seluruh distribusi LibreOffice. Perangkat tujuan Windows x64 tidak perlu memasang Python, dependency Python, atau LibreOffice secara terpisah. Folder LibreOffice tidak perlu disimpan di repository; skrip build menyalin atau mengekstraknya ke paket rilis.

## Persiapan mesin build

Gunakan Windows x64 dan siapkan environment Python proyek:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[packaging]"
```

Unduh MSI LibreOffice Windows x86-64 dari situs resmi atau siapkan folder distribusi LibreOffice yang sudah diekstrak lengkap. Folder sumber harus memuat `program\soffice.exe` atau `program\soffice.com`, beserta resource LibreOffice lainnya.

## Membuat paket

Dengan folder distribusi:

```powershell
.\scripts\build_portable.ps1 -LibreOfficeSource "D:\tools\LibreOffice"
```

Atau langsung dari MSI resmi bertanda tangan valid:

```powershell
.\scripts\build_portable.ps1 -LibreOfficeSource "D:\downloads\LibreOffice_x64.msi"
```

Skrip membuat folder output baru di `dist\portable-<timestamp>\DocuConvert\` dan menaruh distribusi lengkap LibreOffice di `tools\LibreOffice\`. MSI diekstrak sebagai administrative image; tidak dipasang ke Windows mesin build. Output tidak menimpa paket yang sudah ada. Jalankan executable dari folder `dist`, bukan file staging di `build`; file staging tidak menyertakan seluruh DLL dan kini ditandai `DocuConvert-build-only`.

Kirim seluruh folder output (misalnya sebagai ZIP atau lewat installer). Pengguna menjalankan `DocuConvert\DocuConvert.exe`; jangan hanya mengirim executable-nya. Paket ini ditargetkan untuk Windows x64. Sistem operasi atau arsitektur lain membutuhkan runtime LibreOffice dan paket aplikasi yang sesuai.

## Pemeriksaan distribusi

Sebelum rilis, uji paket pada Windows x64 yang tidak memiliki LibreOffice terpasang: buka `DocuConvert.exe`, pastikan Pengaturan menampilkan LibreOffice terdeteksi, lalu konversi DOCX/XLSX/PPTX ke PDF tanpa membuka jendela konsol. Pertahankan direktori `tools\LibreOffice` dan berkas lisensinya saat mengarsipkan. Tinjau kewajiban lisensi dan ketersediaan source code untuk versi yang dibagikan di [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
