# PRD — DocuConvert Desktop

## 1. Ringkasan Produk

**DocuConvert Desktop** adalah aplikasi desktop lokal untuk mengonversi dan mengelola dokumen, dengan pengalaman penggunaan sederhana seperti iLovePDF. Pengguna dapat menarik file ke aplikasi, memilih operasi, menjalankan proses, lalu menyimpan hasilnya tanpa perlu mengunggah dokumen ke server.

Produk ditujukan untuk Windows, macOS, dan Linux. Pengguna mengunduh installer atau paket resmi untuk OS-nya, memasang aplikasi, lalu menjalankan DocuConvert seperti aplikasi desktop biasa. Pemrosesan dokumen dilakukan di perangkat; pengguna tidak perlu memasang Python, menjalankan terminal, atau memahami komponen teknis aplikasi.

## 2. Latar Belakang dan Masalah

Pengguna sering membutuhkan konversi dokumen untuk pekerjaan administrasi, sekolah, bisnis, dan kebutuhan pribadi. Solusi berbasis web memang mudah digunakan, tetapi memiliki beberapa kekurangan:

- dokumen harus diunggah ke layanan pihak ketiga;
- terdapat batas ukuran atau jumlah file;
- kualitas dan format hasil tidak selalu konsisten;
- fitur tertentu berbayar;
- proses bergantung pada koneksi internet.

DocuConvert Desktop menyelesaikan masalah tersebut dengan memproses file secara lokal, menyediakan antarmuka sederhana, dan mengutamakan privasi pengguna.

## 3. Visi Produk

Menjadi aplikasi desktop converter dokumen yang cepat, privat, mudah digunakan, dan dapat diandalkan untuk kebutuhan konversi dokumen sehari-hari.

## 4. Tujuan Produk

### Tujuan utama

1. Menyediakan konversi dokumen lokal tanpa upload ke server.
2. Menyederhanakan alur konversi menjadi beberapa langkah yang jelas.
3. Menyediakan fondasi modular agar format dan fitur baru mudah ditambahkan.
4. Menyediakan paket distribusi yang mudah dipasang untuk setiap OS yang didukung.
5. Menyertakan atau menyiapkan dependency aplikasi secara transparan agar pengguna tidak perlu mengatur runtime secara manual.

### Sasaran terukur MVP

- Pengguna baru dapat melakukan konversi pertama dalam maksimal 3 langkah.
- Konversi DOCX ke PDF berhasil pada minimal 95% dokumen uji umum.
- Aplikasi tetap responsif ketika proses konversi sedang berjalan.
- Tidak ada file pengguna yang dikirim keluar dari komputer.
- Semua error utama ditampilkan dalam bahasa yang mudah dipahami.
- Pengguna awam dapat mengunduh, memasang, dan menjalankan aplikasi tanpa alat developer atau langkah setup teknis.

## 5. Sasaran Pengguna

### Persona utama

**Staf administrasi**

Membutuhkan konversi Word, Excel, dan PowerPoint ke PDF untuk mengirim dokumen resmi.

**Pelajar dan mahasiswa**

Membutuhkan penggabungan, pemisahan, kompresi, dan konversi dokumen untuk tugas.

**Pemilik usaha kecil**

Membutuhkan pemrosesan invoice, proposal, formulir, dan dokumen pelanggan secara privat.

### Persona sekunder

- pengguna rumahan;
- guru dan tenaga pendidikan;
- operator kantor;
- pengguna yang bekerja dengan dokumen scan.

## 6. Ruang Lingkup Produk

### 6.1 Fitur MVP

#### A. Konversi dokumen

- DOCX ke PDF;
- XLSX ke PDF;
- PPTX ke PDF;
- ODT ke PDF;
- PDF ke DOCX dengan batasan kualitas yang dijelaskan kepada pengguna;
- JPG/PNG ke PDF;
- PDF ke JPG/PNG.

#### B. Operasi PDF

- menggabungkan beberapa PDF;
- memisahkan halaman PDF berdasarkan rentang halaman;
- mengekstrak halaman tertentu;
- mengompres PDF;
- memutar halaman;
- menghapus halaman;
- menambahkan watermark teks;
- menambahkan password sederhana pada PDF jika library yang dipilih mendukungnya.

#### C. Pengalaman pengguna

- drag-and-drop file;
- pemilih file native;
- daftar file yang dipilih;
- validasi ekstensi dan ukuran file;
- progress bar;
- tombol batal;
- notifikasi berhasil atau gagal;
- pilihan lokasi output;
- membuka folder output setelah selesai;
- riwayat proses lokal;
- mode terang dan gelap mengikuti preferensi aplikasi.
- installer/paket distribusi untuk Windows, macOS, dan Linux yang masuk daftar platform resmi.
- runtime aplikasi dan dependency yang diperlukan tersedia melalui paket atau proses instalasi resmi; tidak meminta pengguna memasang Python atau dependency manual.

### 6.2 Fitur fase berikutnya

- OCR untuk PDF hasil scan;
- batch conversion seluruh folder;
- template nama file output;
- preview halaman PDF;
- kompresi dengan beberapa preset kualitas;
- enkripsi dan decrypt PDF;
- dukungan CSV, TXT, HTML, EPUB, dan format gambar tambahan;
- plugin converter pihak ketiga;
- update otomatis;
- dukungan OS di luar platform resmi yang ditetapkan;
- telemetri opt-in yang tidak mengandung isi dokumen.

### 6.3 Di luar scope MVP

- pengeditan isi dokumen seperti Microsoft Word;
- kolaborasi realtime;
- penyimpanan cloud;
- login akun;
- sinkronisasi antarperangkat;
- layanan API publik;
- jaminan kesetiaan 100% pada konversi PDF ke DOCX;
- pemrosesan dokumen yang dilindungi DRM atau password tanpa izin pengguna.

### 6.4 Target distribusi

- **Windows:** installer per-user `.exe` untuk Windows x64; membuat Start Menu shortcut dan uninstaller.
- **macOS:** installer `.pkg` terpisah untuk Intel x64 dan Apple Silicon arm64; signing dan notarization diperlukan sebelum distribusi publik yang mulus.
- **Linux:** paket `.deb` untuk Ubuntu 22.04+/Debian 12+ x86_64; dependency LibreOffice dan runtime desktop dikelola oleh package manager.
- Setiap OS dan arsitektur memiliki artifact build tersendiri. Satu file `.exe` bukan paket universal untuk Windows, macOS, dan Linux.
- Package mencakup runtime aplikasi dan dependency yang dibutuhkan, atau menjalankan instalasi dependency tanpa meminta pengguna melakukan setup manual.
- LibreOffice tidak boleh menjadi prasyarat tersembunyi. Untuk konversi Office, keputusan bundling, adapter alternatif, ukuran paket, dan kepatuhan lisensi harus diselesaikan sebelum rilis; jika suatu fitur memang belum tersedia, UI menyatakannya sebelum pengguna mengandalkan fitur tersebut.
- Setelah instalasi selesai, fitur yang dinyatakan tersedia harus bisa digunakan tanpa koneksi internet. Internet hanya diperlukan untuk mengunduh installer dan, bila kelak ditambahkan, update yang dipilih pengguna.

## 7. Prinsip Produk

1. **Local-first** — file diproses di perangkat pengguna.
2. **Privacy by default** — tidak ada upload, tracking, atau analisis isi dokumen pada MVP.
3. **Simple by default** — alur utama harus mudah dipahami pengguna nonteknis.
4. **Fail safely** — file asli tidak pernah ditimpa secara default.
5. **Modular** — setiap jenis konversi diimplementasikan sebagai adapter yang dapat diuji secara terpisah.
6. **Transparent quality** — aplikasi menjelaskan jika hasil konversi memiliki keterbatasan.

## 8. User Stories

### Konversi

- Sebagai pengguna, saya ingin memilih file DOCX agar dapat mengubahnya menjadi PDF.
- Sebagai pengguna, saya ingin mengubah beberapa file Office sekaligus agar pekerjaan lebih cepat.
- Sebagai pengguna, saya ingin mengubah PDF menjadi DOCX agar dapat mengedit kontennya.
- Sebagai pengguna, saya ingin mengubah gambar menjadi PDF agar dapat mengirim dokumen dalam satu file.

### Operasi PDF

- Sebagai pengguna, saya ingin menggabungkan beberapa PDF menjadi satu dokumen.
- Sebagai pengguna, saya ingin mengambil halaman tertentu dari PDF.
- Sebagai pengguna, saya ingin mengurangi ukuran PDF agar mudah dikirim melalui email.
- Sebagai pengguna, saya ingin memutar atau menghapus halaman yang salah.

### Keamanan dan kontrol

- Sebagai pengguna, saya ingin mengetahui lokasi file hasil.
- Sebagai pengguna, saya ingin membatalkan proses yang sedang berjalan.
- Sebagai pengguna, saya ingin file asli tetap utuh.
- Sebagai pengguna, saya ingin tahu jika file rusak, password-protected, atau tidak didukung.
- Sebagai pengguna nonteknis, saya ingin mengunduh paket untuk OS saya, menginstalnya, lalu langsung menggunakan fitur yang tersedia tanpa memasang runtime atau dependency sendiri.

## 9. Alur Pengguna Utama

### 9.0 Unduh, instal, dan mulai menggunakan aplikasi

1. Pengguna membuka halaman unduhan resmi dan memilih paket sesuai OS/perangkatnya.
2. Pengguna mengunduh installer/paket; halaman unduhan menyebutkan versi OS dan arsitektur yang didukung.
3. Pengguna menjalankan installer atau membuka paket distribusi, menyelesaikan langkah instalasi standar, lalu memasang DocuConvert.
4. Installer menyiapkan runtime, dependency, shortcut/menu aplikasi, dan uninstaller sesuai OS; pengguna tidak perlu membuka terminal atau memasang Python/LibreOffice secara manual.
5. Pengguna membuka DocuConvert dari launcher/menu aplikasi dan dapat langsung menggunakan fitur yang tersedia.
6. Jika dependency tidak dapat dibundel karena ukuran, lisensi, atau batasan OS, aplikasi mengidentifikasinya dengan jelas dan menawarkan instruksi sederhana. Kondisi ini harus diselesaikan sebelum fitur terkait dijanjikan sebagai siap pakai.

Installer dapat diunduh melalui internet, tetapi pemrosesan file setelah instalasi harus berjalan lokal tanpa mengharuskan koneksi internet.

### 9.1 DOCX ke PDF

1. Pengguna membuka aplikasi.
2. Pengguna memilih kartu **Word ke PDF** atau menyeret file ke area drop.
3. Aplikasi memvalidasi file.
4. Pengguna memilih folder output.
5. Aplikasi menjalankan LibreOffice secara background.
6. Progress ditampilkan.
7. File PDF dibuat dengan nama aman dan tidak menimpa file sumber.
8. Pengguna dapat membuka file atau folder hasil.

### 9.2 Menggabungkan PDF

1. Pengguna membuka fitur **Gabungkan PDF**.
2. Pengguna menambahkan beberapa file PDF.
3. Pengguna mengatur urutan dengan drag-and-drop.
4. Pengguna menekan **Gabungkan**.
5. Aplikasi menghasilkan satu PDF output.

### 9.3 PDF ke DOCX

1. Pengguna memilih file PDF.
2. Aplikasi mendeteksi apakah PDF berbasis teks atau scan.
3. Jika PDF scan, aplikasi menampilkan rekomendasi OCR pada fase yang sudah tersedia.
4. Aplikasi menjalankan adapter PDF-to-DOCX.
5. Aplikasi menampilkan peringatan bahwa layout kompleks mungkin berubah.
6. Hasil DOCX disimpan dan dapat dibuka dari aplikasi.

## 10. Arsitektur Sistem

```text
+-------------------------+
| PySide6 User Interface  |
| Window, dialogs, models  |
+------------+------------+
             |
+------------v------------+
| Application Services    |
| Job manager, validation, |
| progress, cancellation   |
+------------+------------+
             |
+------------v------------+
| Converter Registry       |
| DOCX/PDF, image/PDF,     |
| merge, split, compress   |
+------------+------------+
             |
+------------v------------+
| Conversion Adapters      |
| LibreOffice CLI          |
| PyMuPDF / pypdf          |
| Pillow                   |
| PDF-to-DOCX adapter      |
+------------+------------+
             |
+------------v------------+
| Local File System        |
| Input, temporary, output |
| logs, preferences        |
+-------------------------+
```

### 10.1 Lapisan UI

Bertanggung jawab atas:

- menampilkan fitur;
- menerima file;
- menampilkan status job;
- mengelola dialog pengaturan;
- menampilkan error yang ramah pengguna.

UI tidak boleh menjalankan proses konversi berat secara langsung agar aplikasi tidak freeze.

### 10.2 Lapisan Application Service

Bertanggung jawab atas:

- membuat dan mengatur conversion job;
- validasi input;
- menentukan adapter yang sesuai;
- mengelola worker thread;
- mengirim progress dan event status ke UI;
- menangani cancellation dan cleanup.

### 10.3 Lapisan Converter Adapter

Setiap converter mengikuti kontrak umum:

```python
class ConverterAdapter(Protocol):
    def can_handle(self, source: Path, target_format: str) -> bool: ...
    def convert(self, job: ConversionJob, reporter: ProgressReporter) -> ConversionResult: ...
    def validate_environment(self) -> EnvironmentCheck: ...
```

Dengan struktur ini, penambahan converter baru tidak memerlukan perubahan besar pada UI.

### 10.4 Worker dan concurrency

- Gunakan `QThreadPool` dan `QRunnable` atau worker berbasis `QThread`.
- Satu job tidak boleh mengakses widget secara langsung.
- Progress dikirim melalui signal.
- Proses LibreOffice dijalankan melalui `subprocess` tanpa membuka jendela.
- Cancellation harus menghentikan proses turunan dengan aman.
- File sementara dibersihkan setelah job selesai atau dibatalkan.

### 10.5 Packaging dan platform

- Kode aplikasi dan converter memisahkan logika lintas platform dari integrasi khusus OS.
- Build release dibuat per OS pada environment build yang sesuai dan diuji pada OS target; artifact satu OS tidak dianggap dapat menggantikan artifact OS lain.
- Installer menangani runtime, resource Qt, ikon, metadata aplikasi, shortcut/launcher, lokasi konfigurasi, dan uninstall sesuai konvensi OS.
- Deteksi dependency memberi status dan tindakan yang jelas, bukan stack trace atau instruksi terminal kepada pengguna umum.
- Build release diuji dari instalasi bersih, bukan hanya dari environment developer.

## 11. Tech Stack

### Wajib

- **Python 3.12+** — bahasa utama.
- **PySide6** — GUI desktop berbasis Qt.
- **LibreOffice** — konversi DOCX, XLSX, PPTX, ODT ke PDF.
- **PyMuPDF** — membaca, merender, menggabungkan, memisahkan, dan memodifikasi PDF.
- **Pillow** — membaca dan membuat file gambar.
- **pypdf** — operasi PDF sederhana jika dibutuhkan sebagai alternatif.
- **pytest** — unit test dan integration test.
- **Ruff** — linting dan formatting.
- **Packaging tool** — pilih tool yang menghasilkan executable/paket untuk tiap OS; PyInstaller dapat dievaluasi, tetapi satu build tidak diasumsikan berjalan lintas OS.
- **Installer builder per OS** — dipilih setelah strategi bundling, lisensi dependency, dan baseline platform ditetapkan.

### Opsional atau perlu evaluasi lisensi

- **pdf2docx** — kandidat adapter PDF ke DOCX untuk PDF berbasis teks.
- **Tesseract OCR/OCRmyPDF** — fase OCR.
- **QtAwesome atau ikon SVG bawaan** — ikon UI.
- **QSettings** — penyimpanan preferensi aplikasi.

### Catatan lisensi

Lisensi setiap dependency harus diperiksa sebelum distribusi komersial. PyMuPDF memiliki pilihan lisensi yang perlu dievaluasi berdasarkan cara aplikasi didistribusikan. LibreOffice memiliki lisensi open source tersendiri dan binary redistribusinya perlu dipastikan sesuai ketentuan. Keputusan final lisensi harus dicatat sebelum rilis publik.

## 12. Struktur Repository yang Disarankan

```text
docuconvert/
├── app/
│   ├── main.py
│   ├── bootstrap.py
│   ├── config.py
│   ├── domain/
│   │   ├── models.py
│   │   ├── enums.py
│   │   └── errors.py
│   ├── application/
│   │   ├── job_manager.py
│   │   ├── conversion_service.py
│   │   ├── validation_service.py
│   │   └── history_service.py
│   ├── infrastructure/
│   │   ├── libreoffice_runner.py
│   │   ├── filesystem.py
│   │   ├── settings.py
│   │   └── logging_setup.py
│   ├── converters/
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── office_to_pdf.py
│   │   ├── pdf_to_docx.py
│   │   ├── image_to_pdf.py
│   │   ├── pdf_to_image.py
│   │   ├── pdf_merge.py
│   │   ├── pdf_split.py
│   │   └── pdf_compress.py
│   └── ui/
│       ├── main_window.py
│       ├── components/
│       ├── dialogs/
│       ├── models/
│       └── resources/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── test_license_inventory.py
├── docs/
├── scripts/
├── pyproject.toml
├── README.md
└── LICENSE
```

## 13. Model Data Utama

```text
ConversionJob
- id: UUID
- operation: OperationType
- source_files: list[Path]
- output_directory: Path
- output_file: Path | None
- status: queued | running | completed | failed | cancelled
- progress: int
- created_at: datetime
- started_at: datetime | None
- finished_at: datetime | None
- error_code: str | None
- error_message: str | None
```

```text
ConversionResult
- success: bool
- output_files: list[Path]
- warnings: list[str]
- duration_ms: int
- source_file_count: int
```

## 14. Detail Fitur dan Requirement Fungsional

### FR-001 — Dashboard

Dashboard harus menampilkan kartu fitur utama, area drag-and-drop, tombol pemilih file, dan daftar aktivitas terakhir.

### FR-002 — Validasi file

Aplikasi harus memeriksa ekstensi, keberadaan file, akses baca, ukuran file, format yang didukung, dan kemungkinan file rusak.

### FR-003 — Konversi Office ke PDF

Aplikasi harus memanggil LibreOffice dalam mode headless dengan profile temporary yang terisolasi per job.

### FR-004 — Penggabungan PDF

Aplikasi harus menerima minimal dua PDF, mempertahankan urutan pengguna, dan menghasilkan satu file output.

### FR-005 — Pemisahan PDF

Aplikasi harus mendukung rentang seperti `1-3`, halaman tunggal seperti `5`, serta kombinasi seperti `1-3,5,8-10`.

### FR-006 — Gambar ke PDF

Aplikasi harus menerima JPG dan PNG, menyediakan urutan gambar, dan menghasilkan PDF dengan ukuran halaman yang konsisten.

### FR-007 — PDF ke gambar

Aplikasi harus memungkinkan pemilihan format PNG atau JPG dan resolusi output yang wajar.

### FR-008 — Penamaan output

Aplikasi harus membuat nama output yang aman, mencegah overwrite, dan menawarkan suffix seperti `_converted`, `_merged`, atau `_compressed`.

### FR-009 — Progress dan pembatalan

Setiap job harus memiliki status, progress jika tersedia, tombol batal, dan pesan hasil akhir.

### FR-010 — Error handling

Error teknis harus dicatat ke log, tetapi UI menampilkan pesan ringkas, penyebab yang mungkin, dan tindakan yang dapat dilakukan pengguna.

### FR-011 — Riwayat

Riwayat lokal hanya menyimpan metadata job dan lokasi file, bukan isi dokumen.

### FR-012 — Deteksi dependency

Aplikasi harus memeriksa dependency fitur, mengutamakan versi yang dikelola melalui distribusi resmi, dan menjelaskan fitur/tindakan yang tersedia jika dependency tidak ditemukan. LibreOffice tidak boleh menjadi prasyarat tersembunyi yang mengharuskan pengguna memasang komponen secara manual.

### FR-013 — Unduhan, instalasi, dan first run

- Pengguna dapat memilih dan mengunduh paket sesuai OS dan arsitektur yang didukung dari halaman distribusi resmi.
- Instalasi tidak memerlukan Python, pip, terminal, atau pengetahuan teknis.
- Paket menyediakan runtime dan resource aplikasi serta shortcut/launcher dan mekanisme uninstall sesuai OS.
- Fitur yang dipasarkan sebagai tersedia dapat digunakan setelah instalasi tanpa dependency tersembunyi atau koneksi internet.
- Jika dependency opsional tidak tersedia, aplikasi menjelaskan fitur yang terdampak dan tindakan yang mudah dilakukan; fitur lain yang tersedia tetap dapat digunakan.
- Setiap paket memiliki versi, catatan rilis, checksum, dan informasi OS/arsitektur minimum.

## 15. Requirement Nonfungsional

### Performa

- UI tidak boleh freeze selama konversi.
- Startup target maksimal 3 detik pada komputer standar, tidak termasuk pemeriksaan dependency berat.
- File kecil hingga 20 MB harus diproses tanpa langkah tambahan.
- Beberapa job dapat diantrikan, tetapi concurrency default dibatasi agar penggunaan memori terkendali.
- Ukuran unduhan dan kebutuhan storage installer diukur serta ditampilkan sebelum rilis; perubahan ukuran yang signifikan ditinjau.

### Keamanan

- Tidak ada upload file pada MVP.
- Gunakan direktori temporary dengan permission yang sesuai.
- Jangan mengeksekusi file input sebagai program.
- Escape seluruh argument subprocess menggunakan list argument, bukan string shell mentah.
- Bersihkan file temporary.
- Jangan menampilkan path sensitif di log jika tidak diperlukan.
- Jangan menimpa file asli secara default.

### Reliability

- Kegagalan satu file dalam batch tidak boleh merusak file lain.
- Proses yang crash harus menghasilkan status failed, bukan job menggantung.
- Aplikasi harus dapat dibuka kembali setelah proses gagal.
- Instalasi bersih, upgrade versi yang didukung, dan uninstall diuji pada setiap OS resmi; uninstall tidak menghapus file input/output pengguna.

### Usability

- Bahasa UI awal: Bahasa Indonesia.
- Istilah teknis harus dijelaskan dengan bahasa sederhana.
- Tombol utama harus konsisten.
- Area drop harus terlihat jelas.
- Kontras dan ukuran font harus dapat dibaca.

### Maintainability

- Converter tidak boleh bergantung pada widget UI.
- Semua converter memiliki unit test.
- Semua operasi file penting memiliki integration test.
- Dependency dan lisensi didokumentasikan.
- Build packaging per OS otomatis dan tidak mencampur konfigurasi khusus platform ke dalam converter domain.

## 16. UX dan Navigasi

### Menu utama

- Beranda
- Semua alat
- Riwayat
- Pengaturan
- Tentang

### Kartu alat MVP

- Word ke PDF
- Excel ke PDF
- PowerPoint ke PDF
- PDF ke Word
- Gabungkan PDF
- Pisahkan PDF
- Kompres PDF
- Gambar ke PDF
- PDF ke Gambar

### State UI

1. Empty — belum ada file.
2. Selected — file sudah dipilih, menunggu konfigurasi.
3. Validating — file sedang diperiksa.
4. Processing — konversi berjalan.
5. Completed — output tersedia.
6. Failed — proses gagal dengan opsi retry.
7. Cancelled — proses dibatalkan dan temporary file dibersihkan.

## 17. Strategi Konversi

### Office ke PDF

LibreOffice dijalankan dalam mode headless. Setiap job menggunakan temporary user profile agar proses tidak saling mengganggu dan tidak menggunakan profile desktop pengguna secara langsung.

### PDF ke DOCX

Gunakan adapter khusus untuk PDF berbasis teks. Untuk PDF dengan layout kompleks, tabel, kolom, font khusus, atau scan, tampilkan peringatan kualitas. Hasil harus diberi status warning jika struktur tidak dapat dipertahankan sempurna.

### PDF ke gambar

Render tiap halaman dengan PyMuPDF. Pengguna dapat memilih format PNG atau JPG serta resolusi standar.

### Gambar ke PDF

Normalisasi orientasi gambar, mode warna, dan metadata sebelum memasukkan gambar ke PDF. Nama output harus aman dan urutan gambar harus mengikuti daftar pengguna.

### Kompres PDF

Sediakan preset awal:

- Rendah — kualitas paling kecil, file lebih ringan.
- Seimbang — rekomendasi default.
- Tinggi — mempertahankan kualitas lebih baik.

Hasil kompresi harus dibandingkan dengan file sumber. Jika hasil lebih besar, aplikasi dapat menawarkan untuk mempertahankan file sumber atau tetap menggunakan hasil.

## 18. Task Pengembangan

### Phase 0 — Discovery dan fondasi

- [ ] Finalisasi nama, ikon, dan identitas aplikasi.
- [ ] Tetapkan OS/arsitektur minimum resmi untuk Windows, macOS, dan Linux serta baseline distro Linux.
- [ ] Inventaris dependency dan lisensi.
- [ ] Buat repository dan aturan branching.
- [ ] Buat konfigurasi Python, Ruff, pytest, dan logging.
- [ ] Buat skeleton aplikasi PySide6.

### Phase 1 — Shell aplikasi dan desain UI

- [ ] Buat main window.
- [ ] Buat sidebar atau navigasi utama.
- [ ] Buat dashboard kartu fitur.
- [ ] Buat reusable drop zone.
- [ ] Buat file list widget.
- [ ] Buat status bar dan notification system.
- [ ] Implementasikan tema terang dan gelap.

### Phase 2 — Job engine

- [ ] Buat `ConversionJob` dan `ConversionResult`.
- [ ] Buat registry converter.
- [ ] Buat queue job.
- [ ] Buat worker thread.
- [ ] Buat signal progress, success, failure, dan cancellation.
- [ ] Buat temporary directory manager.
- [ ] Buat output naming service.

### Phase 3 — Konverter inti

- [ ] Implementasikan Office ke PDF.
- [ ] Implementasikan PDF merge.
- [ ] Implementasikan PDF split.
- [ ] Implementasikan PDF compress.
- [ ] Implementasikan image ke PDF.
- [ ] Implementasikan PDF ke image.
- [ ] Implementasikan PDF ke DOCX dengan adapter yang dipilih.

### Phase 4 — Pengalaman pengguna

- [ ] Tambahkan dialog output directory.
- [ ] Tambahkan preview ringkas metadata file.
- [ ] Tambahkan tombol buka file dan buka folder.
- [ ] Tambahkan retry job.
- [ ] Tambahkan history lokal.
- [ ] Tambahkan dialog dependency LibreOffice.
- [ ] Tambahkan pesan warning untuk kualitas PDF ke DOCX.

### Phase 5 — Quality assurance

- [ ] Unit test domain dan converter.
- [ ] Integration test dengan LibreOffice.
- [ ] Test dokumen kecil, besar, rusak, dan password-protected.
- [ ] Test batch conversion.
- [ ] Test cancellation.
- [ ] Test file path dengan spasi dan karakter non-ASCII.
- [ ] Test memory dan waktu proses.
- [ ] Uji manual pada semua OS dan versi minimum yang resmi didukung.

### Phase 6 — Packaging dan rilis

- [x] Tentukan strategi bundling runtime dan dependency per OS; tidak ada prasyarat developer.
- [ ] Evaluasi lisensi, ukuran, update, dan system dependency untuk setiap paket.
- [x] Buat workflow build artifact terpisah untuk Windows, macOS, dan Linux resmi.
- [x] Implementasikan installer/paket native, shortcut/launcher, dan mekanisme uninstall sesuai OS.
- [ ] Siapkan code signing Windows serta signing dan notarization macOS untuk distribusi publik.
- [ ] Buat halaman unduhan yang membantu memilih paket dan menampilkan versi/arsitektur.
- [x] Buat panduan build dan instalasi per OS; panduan pengguna akhir yang singkat masih perlu dipoles.
- [ ] Buat changelog.
- [ ] Buat smoke test install, launch, fitur dasar, upgrade, dan uninstall pada mesin bersih per OS.
- [x] Buat checksum serta metadata versi/OS/arsitektur untuk setiap artifact.

## 19. Acceptance Criteria MVP

MVP dianggap selesai jika:

1. Pengguna dapat mengunduh paket resmi yang sesuai OS dan arsitekturnya.
2. Pengguna nonteknis dapat memasang dan membuka aplikasi tanpa Python, terminal, atau setup dependency manual.
3. Instalasi bersih, shortcut/launcher, upgrade yang didukung, dan uninstall lolos smoke test pada setiap OS resmi.
4. Uninstall tidak menghapus dokumen input maupun output pengguna.
5. Fitur yang ditandai tersedia berjalan lokal tanpa koneksi internet setelah instalasi.
6. Aplikasi menjelaskan dependency/fitur yang tidak tersedia sebelum pengguna memulai proses.
7. DOCX, XLSX, dan PPTX dapat dikonversi ke PDF pada OS resmi jika fitur Office dinyatakan tersedia.
8. PDF dapat digabung dan dipisah.
9. JPG/PNG dapat dikonversi menjadi PDF.
10. PDF dapat dirender menjadi JPG/PNG.
11. PDF ke DOCX tersedia dengan peringatan kualitas.
12. UI tetap responsif dan job dapat dibatalkan tanpa meninggalkan file temporary.
13. File sumber tidak tertimpa tanpa persetujuan eksplisit; error umum ditampilkan dalam Bahasa Indonesia.
14. Test otomatis inti dan smoke test installer per OS berjalan sukses.
15. Artifact rilis menyediakan versi, OS/arsitektur minimum, catatan rilis, dan checksum.

## 20. Test Matrix Minimum

| Area | Skenario | Hasil yang diharapkan |
|---|---|---|
| Office ke PDF | DOCX sederhana | PDF berhasil dibuat |
| Office ke PDF | File dengan spasi di path | Berhasil tanpa error path |
| Office ke PDF | LibreOffice tidak terpasang | Pesan dependency jelas |
| Packaging | Instalasi bersih per OS | Aplikasi membuka dan fitur paket berjalan tanpa Python/terminal |
| Packaging | Uninstall per OS | Aplikasi terhapus tanpa menghapus dokumen pengguna |
| Offline runtime | Jalankan fitur setelah instalasi tanpa internet | Fitur yang tersedia tetap memproses lokal |
| PDF merge | Dua PDF | Satu PDF sesuai urutan |
| PDF split | Rentang `1-3,5` | Halaman sesuai pilihan |
| Gambar ke PDF | JPG dan PNG | PDF valid dibuat |
| PDF ke gambar | PDF multi-halaman | Satu gambar per halaman |
| PDF ke DOCX | PDF teks | DOCX dapat dibuka |
| Validation | File rusak | Job gagal dengan pesan jelas |
| Cancellation | Batalkan job besar | Proses berhenti dan cleanup berjalan |
| Batch | Satu file gagal | Job lain tetap diproses |
| Security | Input dengan nama aneh | Tidak ada command injection |

## 21. Risiko dan Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| PDF ke DOCX tidak mempertahankan layout | Tinggi | Warning kualitas, adapter modular, test dokumen umum |
| Dependency eksternal belum tersedia | Tinggi | Bundling, adapter alternatif, atau nyatakan fitur tidak tersedia sebelum rilis; jangan jadikan setup manual sebagai kejutan |
| Ukuran installer besar | Sedang | Optimalkan resource dan ukur ukuran unduhan; evaluasi paket tanpa mengaburkan dependency wajib |
| Perbedaan perilaku OS | Tinggi | Build native per OS, abstraction layer, dan smoke/integration test pada semua OS resmi |
| Installer diblokir peringatan OS | Sedang | Code signing/notarization untuk distribusi publik dan checksum resmi |
| Proses berat membuat UI freeze | Tinggi | Worker thread dan queue |
| Perbedaan versi LibreOffice | Sedang | Compatibility check dan integration test pada versi target |
| File password-protected | Sedang | Deteksi dan minta password hanya jika fitur mendukung |
| Lisensi dependency | Tinggi | License inventory dan review sebelum distribusi |
| Output rusak karena crash | Tinggi | Tulis ke temporary output lalu rename saat sukses |
| File sementara tertinggal | Sedang | Cleanup pada success, failure, cancellation, dan startup berikutnya |
| Path non-ASCII | Sedang | Test Windows dengan nama dan folder Bahasa Indonesia |

## 22. Observability dan Logging

Logging lokal harus mencatat:

- waktu job;
- jenis operasi;
- jumlah file;
- durasi;
- status akhir;
- error code;
- versi aplikasi dan dependency.

Logging tidak boleh mencatat isi dokumen. Path lengkap sebaiknya disamarkan atau hanya dicatat ketika diperlukan untuk debugging.

Mode log:

- normal: error dan warning penting;
- debug: detail proses untuk troubleshooting;
- support bundle: ekspor log dan informasi environment tanpa menyertakan dokumen.

## 23. Konfigurasi dan Penyimpanan Lokal

Gunakan `QSettings` atau file konfigurasi lokal untuk:

- tema;
- bahasa;
- folder output default;
- preset kompresi;
- jumlah riwayat yang disimpan;
- preferensi membuka folder setelah selesai.

Riwayat sebaiknya disimpan sebagai SQLite ringan atau JSON metadata. Isi dokumen tidak pernah disimpan ke database.

## 24. Keputusan Produk yang Masih Harus Ditetapkan

- Nama final dan branding.
- Pilihan packaging tool, format artifact final, dan baseline versi/arsitektur setiap OS.
- Strategi converter Office: bundling LibreOffice yang sesuai lisensi/ukuran atau adapter alternatif; dependency tidak boleh menjadi setup manual tersembunyi.
- Distro Linux yang dijamin serta pilihan paket awal seperti AppImage dan/atau `.deb`.
- Kanal distribusi resmi, code signing, notarization, dan kebijakan update aplikasi.
- Apakah fitur PDF ke DOCX tersedia sejak MVP atau masuk fase beta.
- Apakah aplikasi akan gratis, freemium, atau berlisensi komersial.
- Apakah password PDF didukung pada rilis pertama.
- Batas ukuran file yang direkomendasikan untuk pengalaman pengguna.

## 25. Definition of Done

Sebuah fitur dinyatakan selesai jika:

- alur UI tersedia;
- service dan adapter tidak bergantung langsung pada widget;
- validasi input tersedia;
- error dan cancellation ditangani;
- unit test dan integration test tersedia;
- log tidak membocorkan isi dokumen;
- dokumentasi penggunaan diperbarui;
- fitur diuji pada build development dan installer;
- lisensi dependency yang relevan telah dicatat.

## 26. Rekomendasi Urutan Implementasi

Urutan paling aman untuk membangun produk:

1. Shell PySide6 dan desain dashboard.
2. Job engine, worker, progress, dan cancellation.
3. Office ke PDF melalui LibreOffice.
4. Merge dan split PDF.
5. Gambar ke PDF dan PDF ke gambar.
6. Kompres PDF.
7. PDF ke DOCX sebagai fitur dengan status beta.
8. History, settings, logging, lalu installer lintas platform dan uji instalasi bersih.
9. OCR dan batch folder pada fase berikutnya.

Dengan urutan ini, produk sudah memberikan manfaat nyata sejak awal, sementara bagian paling sulit—PDF ke DOCX dan OCR—dapat dikembangkan secara terisolasi tanpa mengganggu fondasi aplikasi.
