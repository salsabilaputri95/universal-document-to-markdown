# ⚡ OmniMark

> **Universal Document to Markdown — Local-First, Fast, and Secure**

**OmniMark** adalah aplikasi desktop-web lokal modern untuk mengonversi berbagai format dokumen bisnis, akademik, dan teknis (`.pdf`, `.docx`, `.xlsx`, `.pptx`, `.csv`) menjadi Markdown (`.md`) berkualitas tinggi. Aplikasi dirancang dengan prinsip **local-first** dan **struktur-terjaga**, memastikan dokumen diproses secara offline di komputer lokal tanpa mengirim data pengguna ke cloud atau layanan pihak ketiga.

---

## 📑 Daftar Isi

- [Tujuan Aplikasi](#-tujuan-aplikasi)
- [Fitur Utama](#-fitur-utama)
- [Format Dokumen yang Didukung](#-format-dokumen-yang-didukung)
- [Teknologi yang Digunakan](#-teknologi-yang-digunakan)
- [Struktur Folder Proyek](#-struktur-folder-proyek)
- [Persyaratan Sistem](#-persyaratan-sistem)
- [Panduan Instalasi](#-panduan-instalasi)
  - [Instalasi di Windows 10/11](#instalasi-di-windows-1011)
  - [Instalasi di Ubuntu Linux](#instalasi-di-ubuntu-linux)
- [Konfigurasi Aplikasi](#-konfigurasi-aplikasi)
- [Cara Menjalankan Aplikasi](#-cara-menjalankan-aplikasi)
- [Panduan Penggunaan](#-panduan-penggunaan)
- [Arsitektur &amp; Logika Conversion Engine](#-arsitektur--logika-conversion-engine)
- [Format Output Markdown](#-format-output-markdown)
- [Struktur Ekspor Bundel ZIP](#-struktur-ekspor-bundel-zip)
- [Pengujian Otomatis (Testing)](#-pengujian-otomatis-testing)
- [Troubleshooting &amp; Solusi](#-troubleshooting--solusi)
- [Keterbatasan Konversi](#-keterbatasan-konversi)
- [Keamanan &amp; Privasi Dokumen](#-keamanan--privasi-dokumen)

---

## 🎯 Tujuan Aplikasi

Mengonversi dokumen biner yang terkunci dalam format aplikasi perkantoran menjadi teks **Markdown (.md)** yang mudah dibaca, diindeks, disimpan dalam sistem kontrol versi (Git), atau digunakan untuk *knowledge base* dan *Retrieval-Augmented Generation* (RAG).

Fokus utama OmniMark adalah **mempertahankan struktur dokumen**:

1. Mempertahankan hierarki judul (*Heading 1–6*).
2. Mengonversi data tabel menjadi tabel Markdown terformat rapi.
3. Menjaga urutan paragraf, daftar bernomor (*ordered list*), dan poin peluru (*unordered list*).
4. Mengekstrak gambar dan diagram serta menautkannya dengan *relative path* Markdown yang valid.
5. Menangani lembar kerja Excel multi-sheet dan sel gabungan (*merged cells*).

---

## ✨ Fitur Utama

- **🔒 100% Local-First & Offline**: Tidak memerlukan koneksi internet saat konversi, tanpa database eksternal, tanpa API OpenAI/Gemini/Claude, dan tanpa ketergantungan Ollama.
- **⚡ Smart Engine Selection & Fallback**:
  - **Docling**: Engine utama untuk PDF kompleks, jurnal ilmiah multi-kolom, OCR, dan tabel visual.
  - **Microsoft MarkItDown**: Engine alternatif resmi untuk konversi dokumen standar.
  - **Automatic Mode**: Pemilihan engine otomatis sesuai ekstensi dokumen dengan mekanisme *fallback* transparan jika engine utama mengalami kegagalan.
- **📊 Penanganan Excel Tingkat Lanjut (`ExcelProcessor`)**:
  - Konversi setiap worksheet menjadi bab/bagian Markdown tersendiri.
  - Nilai *merged cells* diduplikasi ke koordinat sel yang tergabung agar representasi tabel tetap utuh.
  - Nilai formula diambil dari *cached values*; jika belum dihitung, formula asli dicatat tanpa mengarang angka palsu.
  - Peringatan (*warning badge*) otomatis jika tabel sangat lebar (>20 kolom).
- **👁️ Optical Character Recognition (OCR) Lokal**:
  - Menggunakan Tesseract OCR lokal yang mendukung Bahasa Indonesia (`ind`), Inggris (`eng`), dan bilingual (`ind+eng`).
  - Dilengkapi *fallback* otomatis ke RapidOCR berbasis ONNX runtime jika binary Tesseract eksternal tidak ditemukan.
- **🖼️ Ekstraksi Gambar Terkelola**:
  - Gambar disimpan dalam folder terpisah (`<nama_dokumen>_assets/`).
  - Penamaan file aman (`image_001.png`, dll.) tanpa risiko duplikasi nama.
  - Tautan gambar di dalam file Markdown menggunakan *relative path* standar forward-slash.
- **🛡️ Isolasi Kesalahan Pemrosesan Batch**:
  - Konversi multi-file diproses secara serial terkontrol.
  - Jika satu file korup atau rusak, proses konversi file lainnya dalam batch tetap berjalan normal (*error isolation*).
- **🎨 Modern Developer UI (Streamlit)**:
  - Desain minimalis bergaya SaaS developer (Linear/Raycast).
  - Dilengkapi tab preview: *Rendered Markdown*, *Markdown Source Code*, dan *Galeri Gambar*.
  - Dasbor metrik real-time (jumlah berhasil, gagal, durasi, dan total ukuran file tanpa angka dummy).
- **📦 Manajer Ekspor Fleksibel**:
  - Unduh satu file `.md`.
  - Unduh seluruh dokumen dalam satu paket `.zip` yang memuat file Markdown, direktori aset gambar, dan file `metadata.json`.

---

## 📄 Format Dokumen yang Didukung

| Format                           | Ekstensi | Engine Utama              | Kapabilitas Ekstraksi                                                  |
| :------------------------------- | :-------: | :------------------------ | :--------------------------------------------------------------------- |
| **PDF**                    | `.pdf` | IBM Docling / MarkItDown  | Heading, paragraf, layout 2 kolom, tabel visual, OCR dokumen scan      |
| **Microsoft Word**         | `.docx` | MarkItDown / Docling      | Heading 1–6, pemformatan bold/italic, bullet/numbered list, tabel     |
| **Microsoft Excel**        | `.xlsx` | ExcelProcessor (OpenPyXL) | Multi-worksheet, merged cells, cached formulas, date/number formatting |
| **Microsoft PowerPoint**   | `.pptx` | MarkItDown / Docling      | Teks per slide, slide headers, list berbutir                           |
| **Comma-Separated Values** | `.csv` | MarkItDown                | Tabel data tabular terstruktur dengan pembatas pipa Markdown           |

---

## 🛠️ Teknologi yang Digunakan

| Komponen                                | Pustaka / Alat         |  Versi Teruji  | Fungsi                                                 |
| :-------------------------------------- | :--------------------- | :-------------: | :----------------------------------------------------- |
| **Bahasa Pemrograman**            | Python (CPython)       | 3.13.5 (64-bit) | Runtime inti aplikasi                                  |
| **Antarmuka Pengguna**            | Streamlit              |     1.66.1     | Framework dashboard desktop-web responsif              |
| **Document Engine (Primary)**     | Docling                |     2.145.0     | Analisis tata letak dokumen, tabel kompleks, OCR       |
| **Document Engine (Alternative)** | Microsoft MarkItDown   |      0.1.9      | Ekstraksi konten cepat multi-format                    |
| **Spreadsheet Processing**        | OpenPyXL & Pandas      |  3.1.5 / 3.1.0  | Pengolahan Excel multi-sheet & merged cells            |
| **Pemrosesan Gambar**             | Pillow (PIL)           |     13.0.0     | Validasi dan penyimpanan format gambar aset            |
| **Utilitas OCR Eksternal**        | Tesseract OCR          |     v5.5.3     | Optical Character Recognition lokal (`ind`, `eng`) |
| **Utilitas PDF Eksternal**        | Poppler (`pdftoppm`) |    v26.09.0    | Rendering dan konversi halaman PDF                     |
| **Pengujian Otomatis**            | Pytest                 |      9.2.0      | Test runner (28 skenario pengujian unit & integrasi)   |
| **Linter & Formatter**            | Ruff                   |     0.17.3     | Pemeriksaan kepatuhan kode dan PEP 8                   |

---

## 📂 Struktur Folder Proyek

Proyek ini dibangun secara modular dengan memisahkan logika antarmuka, pemrosesan dokumen, konfigurasi, dan utilitas:

```text
universal-document-to-markdown/
│
├── app.py                      # Main entrypoint aplikasi Streamlit
├── run.bat                     # Launcher satu klik untuk Windows (aktivasi .venv)
├── pyproject.toml              # Konfigurasi metadata paket, Ruff, dan Pytest
├── requirements.txt            # Daftar pustaka Python yang teruji
├── .gitignore                  # Pengecualian cache, direktori data, dan agent.md
├── README.md                   # Dokumentasi teknis proyek
│
├── .streamlit/
│   └── config.toml             # Konfigurasi tema UI Streamlit (Light mode default)
│
├── config/                     # Pengaturan konfigurasi terpusat
│   ├── __init__.py
│   └── settings.py             # Definisi AppSettings, path direktori, deteksi tools
│
├── core/                       # Inti logika konversi dokumen
│   ├── __init__.py
│   ├── converter.py            # ConversionManager (orkestrasi, batch, fallback)
│   ├── docling_engine.py       # Wrapper IBM Docling (CPU & pipeline OCR)
│   ├── markitdown_engine.py    # Wrapper Microsoft MarkItDown
│   ├── excel_processor.py      # Pengolah Excel multi-sheet, formulas & merged cells
│   ├── file_validator.py       # Validator format, magic bytes, file kosong, password
│   ├── image_processor.py      # Ekstraksi, penamaan aman & relative path gambar
│   └── export_manager.py       # Pembuat output single .md & arsip ZIP
│
├── components/                 # Komponen antarmuka modular (Streamlit)
│   ├── __init__.py
│   ├── sidebar.py              # Navigasi halaman & ringkasan status sistem
│   ├── uploader.py             # Area upload & tabel pra-validasi dokumen
│   ├── settings_panel.py       # Panel pengaturan engine, OCR, dan style Markdown
│   ├── preview.py              # Komponen preview (Rendered, Source, Gambar)
│   ├── result_card.py          # Kartu status konversi per file
│   └── history.py              # Halaman riwayat sesi konversi pengguna
│
├── utils/                      # Pustaka utilitas pendukung
│   ├── __init__.py
│   ├── file_utils.py           # Sanitasi nama Windows, path traversal, ukuran file
│   ├── markdown_utils.py       # Penghitung statistik dokumen & formatter Markdown/RAG
│   ├── zip_utils.py            # Pembuat file ZIP & verifikasi integritas arsip
│   └── logger.py               # Logger rotasi file tanpa membocorkan konten sensitif
│
├── tests/                      # Rangkaian pengujian otomatis (28 tests)
│   ├── __init__.py
│   ├── test_converter.py       # Uji konversi CSV, XLSX, dan file tidak valid
│   ├── test_document_formats.py# Uji PDF digital, DOCX, PPTX, batch error isolation
│   ├── test_excel_processor.py # Uji multi-sheet, merged cells, sheet kosong
│   ├── test_fallback.py        # Uji simulasi kegagalan Docling beralih ke MarkItDown
│   ├── test_file_utils.py      # Uji sanitasi nama Windows (CON, NUL, path traversal)
│   ├── test_file_validator.py  # Uji deteksi file kosong, corrupt, ekstensi ilegal
│   ├── test_markdown_utils.py  # Uji kalkulasi kata, karakter, dan format RAG
│   ├── test_ui.py              # Uji headless Streamlit startup dan navigasi halaman
│   └── test_zip_utils.py       # Uji integritas pembuatan file ZIP dan metadata
│
├── input/                      # Direktori staging dokumen yang diunggah
├── output/                     # Direktori penyimpanan hasil file .md dan folder aset
├── temp/                       # Direktori kerja isolasi proses sementara
└── logs/                       # Log rotasi aplikasi (logs/app.log)
```

---

## 💻 Persyaratan Sistem

- **Sistem Operasi**:
  - Windows 10 atau Windows 11 (64-bit) — *Disarankan*.
  - Ubuntu 20.04 LTS atau Ubuntu 22.04 LTS.
- **CPU / Processor**:
  - Minimal Dual-Core (2 cores, 4 threads) 2.0 GHz (dioptimalkan untuk pemrosesan CPU lokal, **tanpa mewajibkan GPU NVIDIA**).
- **RAM**:
  - Minimal: 4 GB.
  - Direkomendasikan: 8 GB atau lebih (terutama untuk pemrosesan PDF scan resolusi tinggi).
- **Penyimpanan Disk**:
  - Ruang kosong minimal 3 GB untuk runtime Python virtual environment, dependencies PyTorch CPU, dan cache model layout Docling.

---

## 📦 Panduan Instalasi

### Instalasi di Windows 10/11

1. **Buka PowerShell dan masuk ke direktori proyek:**

   ```powershell
   cd d:\universal-document-to-markdown
   ```
2. **Buat dan aktifkan Python Virtual Environment:**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. **Perbarui pip dan pasang pustaka yang dibutuhkan:**

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Pemasangan Utilitas Eksternal (Opsional namun sangat disarankan untuk OCR dan PDF):**

   - **Tesseract OCR**:
     Unduh installer Windows dari [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki). Pasang pada lokasi default: `C:\Program Files\Tesseract-OCR\tesseract.exe`.
     *(Pastikan mencentang data bahasa tambahan "Indonesian" saat proses instalasi).*
   - **Poppler**:
     Unduh binari Windows dari [Poppler for Windows Releases](https://github.com/oschwartz10612/poppler-windows/releases/). Ekstrak ke `C:\Tools\poppler-...\Library\bin` dan tambahkan jalur binari tersebut ke `PATH` Windows.

---

### Instalasi di Ubuntu Linux

1. **Pasang dependensi sistem operasi melalui apt:**

   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-venv python3-pip tesseract-ocr tesseract-ocr-ind poppler-utils
   ```
2. **Setup virtual environment dan dependencies:**

   ```bash
   cd /path/to/universal-document-to-markdown
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## ⚙️ Konfigurasi Aplikasi

Konfigurasi terpusat didefinisikan pada file **`config/settings.py`**. Anda dapat menyesuaikan konfigurasi default melalui file ini atau melalui *Environment Variables*:

| Konfigurasi              |             Nilai Default             | Keterangan                                                          |
| :----------------------- | :-----------------------------------: | :------------------------------------------------------------------ |
| `MAX_FILE_SIZE_MB`     |                `100`                | Batas ukuran file maksimum yang diperbolehkan (MB)                  |
| `SUPPORTED_EXTENSIONS` | `[.pdf, .docx, .xlsx, .pptx, .csv]` | Daftar ekstensi yang diterima validator                             |
| `DEFAULT_ENGINE`       |              `"auto"`              | Pilihan engine default (`auto`, `docling`, `markitdown`)      |
| `OCR_ENABLED`          |               `True`               | Status aktif/nonaktif OCR pada engine Docling                       |
| `DEFAULT_OCR_LANG`     |             `"ind+eng"`             | Bahasa OCR bawaan (`ind+eng`, `eng`, `ind`)                   |
| `MAX_CONCURRENT_JOBS`  |                 `1`                 | Pembatas konkurensi CPU agar aman untuk RAM terbatas                |
| `LOG_LEVEL`            |              `"INFO"`              | Tingkat logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`)       |
| `TESSERACT_CMD`        |              Auto-detect              | Jalur executable Tesseract OCR (override via env `TESSERACT_CMD`) |
| `POPPLER_PATH`         |              Auto-detect              | Jalur direktori Poppler bin (override via env `POPPLER_PATH`)     |

---

## 🚀 Cara Menjalankan Aplikasi

### Di Windows (Cara Termudah)

Klik ganda file **`run.bat`** di root direktori proyek, atau jalankan melalui PowerShell:

```powershell
.\run.bat
```

Script batch tersebut akan otomatis:

1. Mengarahkan direktori kerja ke folder proyek.
2. Mengaktifkan virtual environment `.venv`.
3. Menjalankan Streamlit web server.

### Cara Manual (Windows / Linux)

```bash
# Aktifkan virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux:
# source .venv/bin/activate

# Jalankan Streamlit
python -m streamlit run app.py
```

Setelah aplikasi berjalan, buka peramban web pada alamat:
👉 **`http://localhost:8501`**

---

## 📖 Panduan Penggunaan

1. **Buka Halaman Konversi**:
   Klik menu **🔄 Convert Documents** pada sidebar navigasi.
2. **Atur Opsi Konversi**:
   - **Conversion Engine**: Pilih *Automatic (Smart Selection)*, *Docling*, atau *Microsoft MarkItDown*.
   - **Markdown Output Style**: Pilih *Standard*, *With Metadata*, *With Image References*, atau *RAG Optimized*.
   - **OCR**: Aktifkan centang OCR jika dokumen berupa scan dan tentukan bahasanya (*Indonesia + Inggris*).
   - **Ekstraksi Gambar**: Centang opsi untuk menyimpan diagram dan gambar dokumen.
3. **Unggah Dokumen**:
   Seret file dokumen ke kotak pengunggah (*drag-and-drop*). Sistem akan otomatis memvalidasi integritas file, tipe MIME, dan ukurannya.
4. **Mulai Konversi**:
   Klik tombol **⚡ Konversi Dokumen Sekarang**. Status progres real-time akan ditampilkan per dokumen.
5. **Tinjau dan Unduh Hasil**:
   - Amati kartu hasil konversi yang menyajikan metrik kata, karakter, durasi proses, dan status fallback.
   - Buka tab **Preview** untuk melihat tampilan rendered, teks sumber Markdown, atau galeri gambar yang diekstrak.
   - Klik **📥 Download .md** untuk mengunduh satu file, atau klik **📦 Download Semua Hasil sebagai ZIP** untuk mengunduh arsip lengkap.

---

## 🧠 Arsitektur & Logika Conversion Engine

OmniMark menggunakan pendekatan *multi-engine coordination* terstruktur:

```
                          [ Dokumen Input ]
                                  │
                       [ core/file_validator.py ]
                                  │
         ┌────────────────────────┴────────────────────────┐
         │ Validasi Lolos?                                 │
         ▼                                                 ▼
       [ Ya ]                                           [ Tidak ]
         │                                                 │
    [ Mode Mesin ]                                   Laporkan Error
         ├── auto ───────────┐                       (Status: Failed)
         ├── docling         │
         └── markitdown      │
                             ▼
                    [ Analisis Ekstensi ]
                             │
     ┌───────────────────────┼───────────────────────┐
     ▼                       ▼                       ▼
  [.xlsx]                 [.csv]            [.pdf / .docx / .pptx]
     │                       │                       │
[ExcelProcessor]       [MarkItDown]            [Docling Engine]
(Multi-sheet,                               (Layout, Tables, OCR)
 Merged cells,                                       │
 Cached formula)                                 Sukses?
                                             ┌───────┴───────┐
                                             ▼               ▼
                                           [ Ya ]         [ Tidak ]
                                             │               │
                                             │      [Fallback Otomatis]
                                             │               │
                                             │          [MarkItDown]
                                             │       (fallback_used=True)
                                             │               │
                                             └───────┬───────┘
                                                     ▼
                                          [ Format Markdown & Assets ]
                                                     ▼
                                          [ Hasil Akhir (.md & ZIP) ]
```

### 1. Aturan Mode Automatic

- **`.xlsx`**: Dialihkan langsung ke `ExcelProcessor` berbasis OpenPyXL untuk memastikan seluruh sheet terbaca, nilai sel gabungan terpelihara, dan nilai formula asli tidak hilang.
- **`.csv`**: Diproses secara cepat menggunakan `MarkItDown`.
- **`.pdf`, `.docx`, `.pptx`**: Diprioritaskan ke **Docling Engine**. Jika Docling mengalami kendala (misal format PDF rusak atau struktur font tidak standar), sistem secara otomatis melakukan *fallback* ke **Microsoft MarkItDown** dan mencatat keterangan fallback pada metadata tanpa menghentikan antrean.

---

## 📝 Format Output Markdown

Pengguna dapat memilih salah satu dari 4 gaya output:

1. **Standard Markdown**:
   Teks bersih hasil ekstraksi sesuai standar GitHub Flavored Markdown (GFM).
2. **With Metadata**:
   Menyertakan blok YAML frontmatter di awal dokumen:
   ```yaml
   ---
   source_file: laporan_keuangan.xlsx
   file_type: .xlsx
   file_size: 45.20 KB
   engine_used: ExcelProcessor
   converted_at: 2026-10-30T15:30:00
   pages_or_sheets: 3
   ---
   ```
3. **With Image References**:
   Mempertahankan tag gambar standar Markdown yang merujuk ke folder aset lokal:
   ```markdown
   ![Diagram Alur](laporan_assets/image_001.png)
   ```
4. **RAG Optimized**:
   Memuat penanda bagian eksplisit (*delimiter tags*) untuk memudahkan *text splitters* dan *chunking* pada pipeline RAG (Retrieval-Augmented Generation) tanpa menjalankan model AI lokal.

---

## 📦 Struktur Ekspor Bundel ZIP

Saat memilih opsi download ZIP, arsip dihasilkan dengan struktur standar:

```text
markdown-export.zip/
│
├── laporan_tahunan.md
├── laporan_tahunan_assets/
│   ├── image_001.png
│   └── image_002.png
│
├── data_penjualan.md
├── data_penjualan_assets/
│
└── metadata.json
```

Contoh file **`metadata.json`**:

```json
{
  "application": "OmniMark",
  "tagline": "Universal Document to Markdown",
  "exported_at": "2026-10-30T15:20:00.000000",
  "total_documents": 2,
  "successful_conversions": 2,
  "failed_conversions": 0,
  "documents": [
    {
      "filename": "laporan_tahunan.docx",
      "extension": ".docx",
      "file_size": "128.50 KB",
      "status": "success",
      "requested_engine": "auto",
      "used_engine": "Docling",
      "fallback_used": false,
      "stats": {
        "characters": 12540,
        "words": 1820,
        "lines": 310
      },
      "duration_seconds": 1.84,
      "warnings": [],
      "converted_at": "2026-10-30 15:20:01"
    }
  ]
}
```

---

## 🧪 Pengujian Otomatis (Testing)

Aplikasi memiliki **28 skenario pengujian komprehensif** menggunakan `pytest` yang mencakup seluruh aspek arsitektur:

Jalankan seluruh pengujian:

```powershell
python -m pytest tests -v
```

Hasil pengujian aktual:

```text
tests/test_converter.py::test_convert_csv PASSED                         [  3%]
tests/test_converter.py::test_convert_xlsx_auto PASSED                   [  7%]
tests/test_converter.py::test_convert_invalid_file PASSED                [ 10%]
tests/test_document_formats.py::test_pdf_digital_conversion PASSED       [ 14%]
tests/test_document_formats.py::test_docx_conversion_with_headings_and_tables PASSED [ 17%]
tests/test_document_formats.py::test_pptx_conversion PASSED              [ 21%]
tests/test_document_formats.py::test_batch_conversion_error_isolation PASSED [ 25%]
tests/test_document_formats.py::test_image_processor_and_reference PASSED [ 28%]
tests/test_excel_processor.py::test_excel_processor_multi_sheet PASSED   [ 32%]
tests/test_fallback.py::test_converter_docling_fallback_to_markitdown PASSED [ 35%]
tests/test_file_utils.py::test_sanitize_filename PASSED                  [ 39%]
tests/test_file_utils.py::test_format_file_size PASSED                   [ 42%]
tests/test_file_utils.py::test_is_safe_path PASSED                       [ 46%]
tests/test_file_utils.py::test_isolated_temp_dir PASSED                  [ 50%]
tests/test_file_validator.py::test_validate_nonexistent_file PASSED      [ 53%]
tests/test_file_validator.py::test_validate_unsupported_extension PASSED [ 57%]
tests/test_file_validator.py::test_validate_empty_file PASSED            [ 60%]
tests/test_file_validator.py::test_validate_valid_csv PASSED             [ 64%]
tests/test_file_validator.py::test_validate_corrupt_pdf PASSED           [ 67%]
tests/test_markdown_utils.py::test_count_markdown_stats PASSED           [ 71%]
tests/test_markdown_utils.py::test_count_markdown_stats_empty PASSED     [ 75%]
tests/test_markdown_utils.py::test_format_markdown_standard PASSED       [ 78%]
tests/test_markdown_utils.py::test_format_markdown_with_metadata PASSED  [ 82%]
tests/test_markdown_utils.py::test_format_markdown_rag PASSED            [ 85%]
tests/test_ui.py::test_ui_initial_render PASSED                          [ 89%]
tests/test_ui.py::test_ui_navigate_pages PASSED                          [ 92%]
tests/test_zip_utils.py::test_zip_creation_and_integrity PASSED          [ 96%]
tests/test_zip_utils.py::test_export_manager_batch_zip PASSED            [100%]

============================= 28 passed in 29.96s =============================
```

Jalankan pemeriksaan kepatuhan kode (*linting*):

```powershell
python -m ruff check .
```

*(Hasil: `All checks passed!` tanpa peringatan).*

---

## ❓ Troubleshooting & Solusi

| Masalah                                     | Kemungkinan Penyebab                                                       | Langkah Solusi                                                                                                                                                                                                |
| :------------------------------------------ | :------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Pesan OCR "Not Found"**             | Executable Tesseract belum terdeteksi di sistem.                           | Pasang installer Tesseract OCR dari [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) atau set environment variable `TESSERACT_CMD`. Jika tidak dipasang, aplikasi otomatis menggunakan RapidOCR. |
| **PDF Scan menghasilkan teks kosong** | Dokumen murni hasil pindai (gambar bitmap) dan OCR dalam kondisi nonaktif. | Buka panel opsi konversi dan centang opsi **Aktifkan OCR**.                                                                                                                                             |
| **File ditolak saat diunggah**        | File berukuran 0 byte (kosong), rusak, atau melebihi 100 MB.               | Periksa apakah dokumen dapat dibuka normal di aplikasi aslinya (MS Word/Excel/Acrobat).                                                                                                                       |
| **File terproteksi sandi**            | Dokumen dilindungi enkripsi password.                                      | Hapus proteksi kata sandi dokumen sebelum mengonversinya.                                                                                                                                                     |
| **Tabel Excel sangat lebar**          | Worksheet memiliki >20 kolom.                                              | Sistem tetap mengonversi seluruh kolom tanpa pemotongan data. Geser horizontal tampilan tabel Markdown untuk melihat seluruh sel.                                                                             |

---

## ⚠️ Keterbatasan Konversi

1. **Dokumen Terenkripsi**: Tidak mendukung pembukaan file Office atau PDF yang dilindungi kata sandi tanpa sandi didekripsi terlebih dahulu.
2. **Kualitas Tulisan Tangan**: OCR dioptimalkan untuk teks cetak digital atau hasil scan dokumen resmi; tulisan tangan bersambung memiliki akurasi yang lebih rendah.
3. **Objek Interaktif PPTX**: Transisi slide, audio latar, animasi, dan video pada presentasi PowerPoint tidak dikonversi ke dalam teks Markdown.

---

## 🛡️ Keamanan & Privasi Dokumen

- **Nir-Koneksi Eksternal**: Selama proses konversi, aplikasi tidak melakukan kontak ke API pihak ketiga manapun.
- **Pencegahan Eksploitasi Jalur (*Anti Path-Traversal*)**: Nama file pengguna melalui sanitasi ketat untuk mencegah karakter ilegal Windows (`<>:"/\|?*`) dan karakter *directory traversal* (`../`).
- **Sanitasi Nama Khusus**: Nama khusus sistem Windows seperti `CON`, `PRN`, `AUX`, `NUL` otomatis diganti dengan identifier unik yang aman.
- **Isolasi Temp Directory**: Berkas sementara diproses di direktori terisolasi `temp/` dan dibersihkan setelah selesai.
- **Logging Bersih**: File log hanya mencatat metadata proses tanpa merekam isi teks sensitif pengguna.
