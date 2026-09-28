# Backend lokal

Backend berada di `app/backend/` dan tetap tidak bergantung pada PySide6. Saat aplikasi desktop berjalan, `app/ui/controllers/job_controller.py` menjadi adapter UI: ia menerjemahkan request form menjadi `ConversionJob`, memindahkan event callback ke thread Qt utama melalui signal, dan mengelola tampilan riwayat. `JobManager` menjalankan job di worker thread.

## Menyiapkan environment

```powershell
python -m pip install -e .
```

Konversi Office memerlukan LibreOffice. `create_backend()` memeriksa LibreOffice dan pdf2docx saat runtime dibuat; hasilnya tersedia di `runtime.environment_checks`. Aplikasi mencari executable di path yang dipilih pengguna, `DOCUCONVERT_LIBREOFFICE_PATH`, folder `tools/LibreOffice/program/` atau `LibreOffice/program/` di samping aplikasi, lalu `PATH` dan lokasi instalasi Windows standar. Untuk distribusi portable, sertakan seluruh distribusi LibreOffice pada salah satu folder tersebut; `soffice.exe` saja tidak cukup karena memerlukan file program dan resource lainnya. Tinjau dan sertakan informasi lisensi/source code yang berlaku sebelum mendistribusikannya.

## Memulai job

```python
from pathlib import Path

from app.backend import ConversionJob, OperationType, create_backend

runtime = create_backend()
unsubscribe = runtime.jobs.subscribe(
    lambda event: print(event.job_id, event.status, event.progress, event.message)
)

job = ConversionJob(
    operation=OperationType.MERGE_PDF,
    source_files=[Path(r"C:\Dokumen\bagian-1.pdf"), Path(r"C:\Dokumen\bagian-2.pdf")],
    output_directory=Path(r"C:\Dokumen\hasil"),
)
runtime.jobs.submit(job)

# Di UI, simpan job.id lalu panggil runtime.jobs.cancel(job.id) untuk membatalkan.
# Event queued dipanggil langsung oleh submit; event berikutnya datang dari worker.
# UI sebaiknya meneruskan event ke main thread Qt melalui signal/slot.
runtime.close(wait_for_jobs=True)
unsubscribe()
```

`submit()` hanya memasukkan job ke antrean; validasi file berjalan di worker supaya pemindaian dokumen besar tidak menghambat thread pemanggil. Status dan event job: `queued`, `running`, `completed`, `failed`, atau `cancelled`. `wait(job.id)` mengembalikan `ConversionResult` bila selesai atau `None` jika proses gagal/dibatalkan.

## Operasi dan opsi

`OperationType` menerima key yang juga dipakai katalog UI:

- `word_to_pdf`, `excel_to_pdf`, `powerpoint_to_pdf`, `odt_to_pdf`: LibreOffice headless; file batch diproses satu per satu.
- `pdf_to_word`: pdf2docx; PDF tanpa teks diberi warning karena OCR berada di luar MVP.
- `image_to_pdf`: `page_size` (`a4`, `letter`, `original`), `orientation` (`auto`, `portrait`, `landscape`).
- `pdf_to_image`: `image_format` (`png`, `jpg`), `dpi` (72–300).
- `merge_pdf`: minimal dua PDF; urutan mengikuti `source_files`.
- `split_pdf`: `page_ranges` seperti `1-3,5,8-10`; `mode` `extract` menghasilkan satu PDF, `ranges` menghasilkan satu PDF per bagian.
- `compress_pdf`: `quality` (`small`, `balanced`, `quality`; `low`/`high` juga diterima).
- `rotate_pdf`: `page_ranges`, `degrees` (90, 180, 270).
- `delete_pages`: `page_ranges`; hasil wajib menyisakan setidaknya satu halaman.
- `watermark_pdf`: `text`, `position` (`center`, `diagonal`, `bottom`), `opacity` (`low`, `medium`, `high`).
- `protect_pdf`: `password` minimal enam karakter; hasil memakai AES-256. Password tidak ditulis ke log atau riwayat.

Operasi PDF menerima `source_password` untuk membuka input yang terkunci. Editan PDF mempertahankan password sumber pada hasil. Konversi ke DOCX atau gambar menampilkan warning karena format hasil tersebut tidak membawa proteksi password PDF. Job memakai folder sementara privat di folder output, lalu menerbitkan hasil secara atomik dengan nama unik agar file lama dan sumber tidak tertimpa. File sementara dibersihkan setelah selesai, gagal, atau dibatalkan; direktori job yatim yang lebih dari 24 jam dibersihkan ketika folder output dipakai lagi.

Semua request UI juga dapat menyertakan `output_name`; nama diterapkan pada file staging sebelum publikasi. Untuk ekspor gambar, nama menjadi awalan dengan nomor halaman; untuk mode pemisahan rentang, nama menjadi awalan masing-masing PDF.

PDF ke Word bergantung pada pdf2docx dan hasilnya dapat mengubah tata letak kompleks. Kompresi menulis hasil terpisah dan memberi warning bila ukurannya tidak lebih kecil dari sumber. PyMuPDF memiliki ketentuan lisensi yang perlu ditinjau sebelum distribusi; LibreOffice juga harus dipaketkan sesuai lisensinya.
