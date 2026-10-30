# MASTER PROMPT — UNIVERSAL DOCUMENT TO MARKDOWN

## 1. ROLE

Bertindak sebagai Senior Python Engineer, Software Architect, Document Processing Engineer, dan UI/UX Developer.

Bangun aplikasi desktop-web lokal bernama **Universal Document to Markdown**, yaitu aplikasi untuk mengonversi berbagai format dokumen menjadi Markdown (`.md`) dengan kualitas ekstraksi dan struktur dokumen yang baik.

Jangan hanya membuat mockup, prototype UI, atau contoh kode. Bangun aplikasi yang benar-benar berfungsi, terintegrasi, dapat dijalankan, dan dapat diuji di lingkungan Ubuntu Linux.

Kerjakan langsung di workspace project yang sedang terbuka di VS Code.

## 2. TUJUAN APLIKASI

Aplikasi harus dapat mengonversi:

- PDF (.pdf) → Markdown (.md)
- Microsoft Word (.docx) → Markdown (.md)
- Microsoft Excel (.xlsx) → Markdown (.md)
- Microsoft PowerPoint (.pptx) → Markdown (.md)
- CSV (.csv) → Markdown (.md)

Fokus utama adalah mempertahankan struktur dan informasi dokumen, bukan sekadar mengambil teks mentah.

Aplikasi harus berjalan secara lokal (local-first), tanpa mengirim dokumen pengguna ke server eksternal.

## 3. BATASAN TEKNOLOGI

Gunakan teknologi berikut:

### Backend
- Python 3.11 atau 3.12.
- Streamlit sebagai framework antarmuka.
- Docling sebagai conversion engine utama.
- Microsoft MarkItDown sebagai conversion engine alternatif.
- Pandas dan OpenPyXL untuk pemeriksaan serta penanganan khusus file Excel jika diperlukan.
- Pillow untuk pemrosesan gambar jika diperlukan.

### Document Processing
- Tesseract OCR untuk kebutuhan OCR.
- Poppler untuk utilitas PDF.
- Docling OCR untuk pemrosesan dokumen hasil scan jika didukung oleh konfigurasi yang tersedia.

### Development
- Git.
- Pytest.
- Ruff.
- Python virtual environment.

### Larangan
- Jangan menggunakan Ollama.
- Jangan menggunakan OpenAI API atau API AI eksternal.
- Jangan menggunakan layanan cloud untuk memproses dokumen.
- Jangan menggunakan database eksternal.
- Jangan mewajibkan NVIDIA GPU.
- Jangan membuat ketergantungan pada layanan berbayar.
- Jangan mengirim dokumen pengguna ke pihak ketiga.

Semua pemrosesan dokumen dilakukan di komputer lokal.

## 4. ARSITEKTUR PROJECT

Gunakan struktur modular berikut:

universal-document-to-markdown/
│
├── .venv/
│
├── app.py
│
├── config/
│   ├── __init__.py
│   └── settings.py
│
├── core/
│   ├── __init__.py
│   ├── converter.py
│   ├── docling_engine.py
│   ├── markitdown_engine.py
│   ├── excel_processor.py
│   ├── file_validator.py
│   ├── image_processor.py
│   └── export_manager.py
│
├── components/
│   ├── __init__.py
│   ├── sidebar.py
│   ├── uploader.py
│   ├── settings_panel.py
│   ├── preview.py
│   ├── result_card.py
│   └── history.py
│
├── utils/
│   ├── __init__.py
│   ├── file_utils.py
│   ├── markdown_utils.py
│   ├── zip_utils.py
│   └── logger.py
│
├── tests/
│
├── input/
├── output/
├── temp/
├── logs/
│
├── .streamlit/
│   └── config.toml
│
├── requirements.txt
├── README.md
├── run.bat
└── .gitignore

Pastikan setiap modul memiliki tanggung jawab yang jelas. Hindari menumpuk seluruh logika aplikasi di `app.py`.

## 5. FITUR UTAMA

### A. Dashboard

Buat dashboard yang menampilkan:
- Jumlah dokumen yang berhasil dikonversi.
- Jumlah dokumen yang gagal dikonversi.
- Jumlah dokumen yang sedang diproses.
- Total ukuran file yang diproses.
- Riwayat konversi selama sesi aplikasi berjalan.

Jangan menggunakan angka statistik palsu atau dummy.

### B. Document Upload

Buat komponen upload dengan fitur:
- Drag and drop.
- Multiple file upload.
- Upload beberapa format sekaligus.
- Validasi ekstensi file.
- Validasi ukuran file.
- Informasi nama file.
- Ukuran file.
- Jenis dokumen.
- Status file.

Format yang diterima:

PDF, DOCX, XLSX, PPTX, CSV.

Berikan pesan kesalahan yang jelas jika format tidak didukung.

### C. Conversion Engine Selection

Sediakan pilihan engine:

1. Docling
2. MarkItDown
3. Automatic

Penjelasan:

**Docling**
- Menjadi pilihan utama.
- Diprioritaskan untuk PDF kompleks, jurnal ilmiah, tabel, gambar, dan layout dokumen.
- Gunakan pemrosesan CPU sebagai konfigurasi default.
- Gunakan OCR jika diperlukan.

**MarkItDown**
- Menjadi alternatif untuk ekstraksi konten dokumen.
- Cocok untuk konversi format dokumen umum.
- Gunakan API resmi versi package yang benar.

**Automatic**
- Tentukan engine berdasarkan format dan karakteristik dokumen.
- Jangan mengklaim dapat mendeteksi kompleksitas dokumen jika belum ada mekanisme untuk melakukannya.
- Gunakan aturan pemilihan engine yang eksplisit dan dapat dijelaskan kepada pengguna.
- Jika engine utama gagal, tawarkan fallback ke engine alternatif.
- Jangan melakukan konversi ulang secara diam-diam tanpa mencatatnya.

Jangan mengasumsikan seluruh format memiliki dukungan dan kualitas yang sama pada setiap engine. Validasi kompatibilitas berdasarkan dokumentasi resmi dan implementasi yang terpasang.

### D. PDF Processing

Untuk PDF, usahakan mempertahankan:
- Heading dan subheading.
- Paragraf.
- Daftar bernomor dan bullet.
- Tabel.
- Gambar.
- Caption.
- Persamaan matematika jika didukung.
- Urutan pembacaan teks.
- Struktur dokumen dua kolom.

Sediakan pengaturan OCR:
- OCR aktif/nonaktif.
- Bahasa Indonesia.
- Bahasa Inggris.
- Indonesia + Inggris.

PDF digital dan PDF hasil scan harus dapat dibedakan atau dijelaskan status penanganannya.

Jangan mengklaim OCR berhasil apabila dokumen tidak menghasilkan teks yang dapat dibaca.

### E. Word Processing

Untuk DOCX, pertahankan:
- Heading 1 sampai Heading 6.
- Paragraf.
- Bold dan italic.
- Ordered list.
- Unordered list.
- Tabel.
- Hyperlink.
- Gambar.
- Caption jika tersedia.

Jaga urutan konten sesuai dokumen sumber sejauh didukung engine.

### F. Excel Processing

Excel merupakan bagian penting dari aplikasi.

Tangani:
- Banyak worksheet.
- Nama worksheet.
- Header tabel.
- Data baris dan kolom.
- Empty cells.
- Merged cells jika memungkinkan.
- Formula dan cached values.
- Angka dan tanggal.
- Sheet yang disembunyikan.
- Sheet kosong.

Konversikan setiap worksheet menjadi bagian Markdown tersendiri.

Contoh hasil:

# Laporan Penjualan

## Worksheet: Januari

| Produk | Jumlah | Harga |
|---|---:|---:|
| Laptop | 5 | 7500000 |
| Mouse | 10 | 150000 |

## Worksheet: Februari

| Produk | Jumlah | Harga |
|---|---:|---:|
| Keyboard | 8 | 250000 |

Tambahkan informasi sumber:
- Nama file.
- Nama worksheet.
- Jumlah baris.
- Jumlah kolom.

Jangan mengubah nilai sel menjadi nilai yang tidak sesuai sumber.

Jika formula tidak memiliki cached value, jangan mengarang hasil perhitungannya. Pertahankan formula sebagai informasi atau berikan penanda bahwa hasilnya tidak tersedia.

Jika tabel terlalu lebar untuk Markdown, berikan peringatan dan pertimbangkan opsi ekspor alternatif, tanpa menghilangkan data secara diam-diam.

### G. Markdown Processing

Buat hasil Markdown yang rapi dan konsisten.

Ketentuan:
- Heading menggunakan sintaks Markdown.
- Tabel menggunakan Markdown Table.
- Daftar menggunakan bullet atau numbering.
- Link tetap berupa hyperlink.
- Gambar menggunakan sintaks Markdown.
- Jangan menghapus konten penting secara otomatis.
- Jangan membuat ringkasan menggunakan AI.
- Jangan mengarang informasi yang tidak terdapat pada sumber.

Sediakan opsi:
- Markdown standar.
- Markdown dengan metadata.
- Markdown dengan referensi gambar.
- Markdown untuk kebutuhan RAG.

Untuk mode RAG, pertahankan heading, metadata sumber, dan batas antarbagian agar dokumen mudah diproses pada tahap berikutnya. Jangan membuat embedding atau menjalankan model AI.

### H. Image Extraction

Jika dokumen mengandung gambar:
- Ekstrak gambar jika didukung engine.
- Simpan gambar pada folder terpisah.
- Gunakan nama file yang aman.
- Hindari nama file duplikat.
- Hubungkan gambar dengan dokumen Markdown menggunakan relative path.
- Pastikan ZIP hasil ekspor menyertakan folder gambar.

Contoh:

```text
output/
├── laporan.md
└── laporan_assets/
    ├── image_001.png
    └── image_002.png
```

Jangan membuat referensi gambar yang menunjuk ke file yang tidak ada.

### I. Preview Markdown

Sediakan dua mode preview:

1. Markdown Source: menampilkan sintaks Markdown asli.
2. Rendered Preview: menampilkan hasil render Markdown.

Tambahkan:
- Copy Markdown.
- Download Markdown.
- Navigasi hasil konversi.
- Informasi jumlah karakter dan kata jika tersedia.

### J. Export Manager

Sediakan:
- Download satu file `.md`.
- Download semua hasil sebagai `.zip`.
- Download gambar hasil ekstraksi.
- Download metadata.
- Export berdasarkan dokumen yang dipilih.

Struktur ZIP:

```text
markdown-export.zip/
│
├── laporan.md
├── laporan_assets/
│   ├── image_001.png
│   └── image_002.png
│
├── jurnal.md
├── jurnal_assets/
│
└── metadata.json
```

Pastikan relative path gambar tetap valid setelah ZIP diekstrak.

## 6. UI/UX DESIGN

Buat desain modern, profesional, minimalis, dan cocok untuk aplikasi produktivitas developer.

Referensi visual:
- Clean SaaS dashboard.
- Linear.
- Notion.
- Raycast.

Karakter desain:
- White/light mode sebagai default.
- Dark mode opsional.
- Sidebar navigasi.
- Layout rapi.
- Typography mudah dibaca.
- Spacing konsisten.
- Tidak terlalu banyak warna.
- Tidak menggunakan efek visual berlebihan.
- Responsif.

Navigasi:

1. Dashboard
2. Convert Documents
3. Conversion History
4. Settings
5. About

Pada halaman Convert Documents, tampilkan:

- Upload area.
- Daftar dokumen.
- Pilihan conversion engine.
- Pengaturan OCR.
- Tombol Convert.
- Progress processing.
- Status setiap file.
- Preview Markdown.
- Download hasil.

Pastikan seluruh tombol dan kontrol benar-benar memiliki fungsi. Jangan membuat elemen UI dekoratif yang terlihat interaktif tetapi tidak bekerja.

## 7. FILE MANAGEMENT DAN SECURITY

Aplikasi harus aman untuk memproses dokumen lokal.

Implementasikan:
- Validasi ekstensi dan MIME type.
- Validasi ukuran file.
- Nama file yang aman.
- Isolasi file sementara per pekerjaan.
- Pembersihan temporary files.
- Penanganan file rusak.
- Penanganan dokumen terenkripsi dengan pesan yang sesuai.
- Penanganan kesalahan permission.
- Pencegahan path traversal.
- Batas penggunaan memori yang wajar.
- Logging tanpa menyimpan isi sensitif dokumen.

Jangan menggunakan `shell=True` untuk memproses nama file pengguna.

Jangan mengeksekusi macro, script, atau formula dari dokumen.

Aplikasi hanya membaca dan mengekstrak isi dokumen.

Jangan menghapus file sumber pengguna secara otomatis.

## 8. PERFORMANCE DAN RESOURCE MANAGEMENT

Aplikasi harus bisa berjalan tanpa GPU NVIDIA.

Prioritaskan:
- CPU processing.
- Penggunaan RAM yang efisien.
- Batch processing secara terkendali.
- Progress indicator.
- Error isolation per file.
- Tidak memuat seluruh dokumen besar ke memori secara tidak perlu.
- Penggunaan cache hanya untuk komponen atau model yang aman untuk di-cache.

Jangan menjalankan seluruh file sekaligus jika berpotensi menghabiskan RAM.

Sediakan pengaturan jumlah pekerjaan paralel dengan default konservatif, idealnya satu proses berat dalam satu waktu.

Berikan peringatan jika file terlalu besar atau pemrosesan membutuhkan resource lebih tinggi.

## 9. CONFIGURATION

Buat konfigurasi terpusat.

Contoh pengaturan:
- Maximum upload size.
- Supported extensions.
- Default conversion engine.
- OCR language.
- OCR enabled.
- Temporary directory.
- Output directory.
- Cleanup policy.
- Logging level.
- CPU processing preference.

Jangan menyebarkan konfigurasi yang sama di banyak file.

## 10. TESTING

Gunakan pytest.

Buat pengujian untuk:

1. PDF digital.
2. PDF hasil scan jika fixture tersedia.
3. DOCX dengan heading dan tabel.
4. XLSX dengan beberapa worksheet.
5. XLSX dengan formula.
6. XLSX dengan merged cells.
7. PPTX.
8. CSV.
9. File kosong.
10. File rusak.
11. File dengan ekstensi tidak didukung.
12. File dengan nama khusus.
13. Export ZIP.
14. Referensi gambar.
15. Error fallback engine.

Gunakan fixture pengujian yang dibuat sendiri dan tidak mengandung data pribadi.

Jangan mengklaim seluruh pengujian berhasil jika belum benar-benar dijalankan.

## 11. DOCUMENTATION

Buat README.md yang menjelaskan:

- Deskripsi aplikasi.
- Fitur.
- Arsitektur.
- Teknologi.
- Persyaratan sistem.
- Instalasi Ubuntu.
- Instalasi dependency.
- Cara menjalankan aplikasi.
- Cara menggunakan aplikasi.
- Penjelasan engine.
- Konfigurasi OCR.
- Struktur output.
- Troubleshooting.
- Keterbatasan konversi.
- Cara menjalankan test.

Buat juga requirements.txt yang sesuai dengan implementasi dan versi package yang telah diuji.

## 12. DEVELOPMENT WORKFLOW

Kerjakan dengan urutan berikut:

**FASE 1 — ENVIRONMENT INSPECTION**

Periksa:
- Sistem operasi.
- Versi Python.
- Versi pip.
- Ketersediaan Git.
- Ketersediaan Tesseract.
- Ketersediaan Poppler.
- Kapasitas resource jika dapat diperiksa.

Jangan mengubah konfigurasi sistem tanpa izin.

Jika dependency belum tersedia, berikan perintah instalasinya.

**FASE 2 — PROJECT INITIALIZATION**

Buat struktur folder dan seluruh file project.

Buat virtual environment jika belum ada.

Pastikan dependency terpasang di environment yang benar.

**FASE 3 — CORE DEVELOPMENT**

Implementasikan:
- File validator.
- Docling engine.
- MarkItDown engine.
- Excel processor.
- Conversion manager.
- Markdown processor.
- Image processor.
- Export manager.

Uji setiap komponen secara terpisah sebelum mengintegrasikannya.

**FASE 4 — UI DEVELOPMENT**

Bangun seluruh halaman Streamlit.

Integrasikan frontend dengan backend yang telah diuji.

**FASE 5 — TESTING**

Jalankan:
- Unit tests.
- Integration tests.
- Conversion tests.
- UI startup test.

Perbaiki seluruh error yang ditemukan.

**FASE 6 — FINALIZATION**

Pastikan:
- Aplikasi dapat dijalankan.
- Seluruh fitur utama berfungsi.
- Tidak ada tombol palsu.
- Tidak ada API eksternal.
- Tidak ada ketergantungan Ollama.
- Output Markdown dapat dibuka.
- ZIP dapat diekstrak.
- Gambar memiliki relative path yang valid.
- README sesuai dengan implementasi.

## 13. ACCEPTANCE CRITERIA

Project dianggap selesai jika:

1. Aplikasi berhasil dijalankan di Ubuntu.
2. PDF berhasil dikonversi menjadi Markdown.
3. DOCX berhasil dikonversi menjadi Markdown.
4. XLSX berhasil dikonversi menjadi Markdown.
5. PPTX dan CSV dapat diproses.
6. Pengguna dapat memilih Docling atau MarkItDown.
7. Batch conversion berjalan.
8. Hasil Markdown dapat di-preview.
9. File `.md` dapat diunduh.
10. ZIP dapat diunduh dan diekstrak.
11. OCR tersedia untuk dokumen scan sesuai konfigurasi.
12. Error satu dokumen tidak menghentikan seluruh batch.
13. Aplikasi tidak mengirim dokumen ke cloud.
14. Pengujian dijalankan dan hasilnya dilaporkan secara jujur.

## 14. RULES UNTUK AI CODING AGENT

Perhatikan aturan berikut:

- Jangan hanya memberikan tutorial atau potongan kode. Implementasikan langsung di workspace.
- Jangan membuat file dummy untuk menyatakan fitur sudah selesai.
- Jangan menghapus kode atau konfigurasi yang sudah ada tanpa memeriksa fungsinya.
- Jangan mengasumsikan library sudah terinstal.
- Periksa dokumentasi resmi library sebelum menggunakan API.
- Jangan menggunakan method atau parameter yang sudah tidak berlaku.
- Jangan membuat seluruh kode dalam satu file.
- Jangan mengabaikan error.
- Jangan mengklaim fitur berhasil sebelum diuji.
- Jangan mengubah file sistem Ubuntu.
- Jangan mengunduh model atau dependency tanpa menjelaskan kebutuhan dan sumbernya.
- Jangan menggunakan layanan cloud.
- Jangan memasukkan Ollama ke dalam project.

Jika menemukan masalah teknis, analisis penyebabnya dan berikan solusi yang sesuai.

Jika ada keputusan arsitektur yang belum jelas, pilih solusi yang paling sederhana, stabil, dan mudah dipelihara.

**PENTING:**

Jangan langsung membuat seluruh project secara terburu-buru.

Mulai dari FASE 1. Periksa environment dan workspace terlebih dahulu. Kemudian lanjutkan secara bertahap sampai seluruh acceptance criteria terpenuhi.

Setelah setiap fase:
1. Laporkan file yang dibuat atau diubah.
2. Jelaskan implementasi yang selesai.
3. Jalankan pengujian yang relevan.
4. Laporkan error atau keterbatasan.
5. Lanjutkan ke fase berikutnya jika tidak ada masalah yang menghalangi.

Target akhir adalah aplikasi Universal Document to Markdown yang benar-benar berfungsi, stabil, modular, lokal, dan siap dikembangkan lebih lanjut.

## WINDOWS DEVELOPMENT ENVIRONMENT — MANDATORY

Project dikembangkan dan dijalankan pada Windows 10/11 menggunakan PowerShell dan Visual Studio Code.

Ketentuan:

1. Gunakan Python 3.11 atau 3.12.
2. Gunakan virtual environment `.venv\Scripts\Activate.ps1`.
3. Semua instalasi Python package harus menggunakan pip di dalam virtual environment.
4. Jangan menggunakan perintah `apt`, `sudo`, atau perintah khusus Ubuntu.
5. Gunakan Windows-compatible file path dengan pathlib.
6. Jangan melakukan hardcode Linux paths.
7. Gunakan environment variables untuk konfigurasi lokasi executable eksternal.
8. Deteksi lokasi Tesseract OCR dan Poppler melalui konfigurasi atau PATH.
9. Jangan mengasumsikan Tesseract dan Poppler otomatis tersedia.
10. Tangani Windows file permission dan temporary directory dengan benar.
11. Pastikan pemrosesan dokumen tidak bergantung pada NVIDIA GPU.
12. Buat `run.bat` sebagai launcher utama.
13. Sediakan perintah PowerShell untuk instalasi dan menjalankan aplikasi.
14. Pastikan ZIP export dan relative image paths kompatibel dengan Windows.
15. Pastikan seluruh dependency dan API library kompatibel dengan Windows.

### Windows Project Launcher

Gunakan `run.bat` untuk menjalankan Streamlit:

```bat
@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m streamlit run app.py
pause
```

### Windows Testing

Jalankan testing menggunakan:

```powershell
python -m pytest tests -v
```

Jalankan pemeriksaan kode menggunakan:

```powershell
python -m ruff check .
```

### Windows Acceptance Criteria

Aplikasi harus:
- Berjalan pada Windows 10/11.
- Tidak membutuhkan WSL.
- Tidak membutuhkan Docker.
- Tidak membutuhkan Ollama.
- Tidak membutuhkan koneksi API.
- Menggunakan local CPU processing.
- Dapat dijalankan melalui run.bat.
- Dapat membaca dan menulis file dengan path Windows secara benar.

Jangan membuat konfigurasi Ubuntu atau Linux kecuali sebagai dokumentasi tambahan yang memang diperlukan.