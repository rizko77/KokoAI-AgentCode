SYSTEM_IDENTITY = """
╔══════════════════════════════════════════════════════╗
║         KokoAI 2.0 - AgentCode                       ║
║         AI Coding Assistant Lokal                    ║
║         By Rizko Imsar, KokoDev Studio               ║
╚══════════════════════════════════════════════════════╝
"""

WELCOME_MESSAGE = """
🚀 Selamat datang di KokoAI 2.0 - AgentCode!

AI Coding Assistant yang berjalan lokal di komputer Anda.
Tanpa API berbayar - menggunakan self-learning AI engine.

📁 Workspace: {workspace}
🧠 Model Status: {model_status}
📊 Knowledge: {knowledge_count} snippets

Langsung ketik apapun untuk memulai! Tidak perlu perintah khusus.
Contoh:
  - "buat file main.py"
  - "cari python sorting algorithm"
  - "jelaskan cara kerja for loop"
  - "cuaca Jakarta"
  - "jam berapa sekarang?"
  - Atau ketik kode langsung untuk mendapat suggestion

Perintah tersedia (opsional):
  /help      - Bantuan lengkap
  /suggest   - Code suggestion
  /train     - Training model
  /search    - Cari di internet
  /stats     - Statistik model
  /mode      - Ganti mode (thinking/reasoning/medium/fast)
  /autotrain - Auto-training dari internet
  /save      - Simpan model
  /exit      - Keluar
"""

HELP_MESSAGE = """
📖 BANTUAN - KokoAI 2.0 AgentCode
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 CARA PAKAI (LANGSUNG KETIK):
  Cukup ketik apapun dalam bahasa Indonesia atau English!

  Contoh:
    "buatkan file calculator.py"     → Buat file baru
    "baca file main.py"              → Tampilkan isi file
    "hapus file test.py"             → Hapus file
    "cari python bubble sort"        → Cari di internet
    "jelaskan cara kerja async"      → Penjelasan kode
    "fix error di main.py"           → Debug
    "buat project web flask"         → Scaffold project
    "jam berapa?"                    → Waktu sekarang
    "cuaca Jakarta"                  → Info cuaca
    def calculate_sum(               → Autocomplete kode

🔧 PERINTAH SLASH (OPSIONAL):
  /suggest <kode>      Autocomplete suggestion
  /complete <kode>     Lengkapi baris kode
  /train <path>        Training dari folder
  /trainfile <file>    Training dari file
  /search <query>      Cari code di internet
  /learn <url>         Belajar dari URL
  /docs <topic>        Cari dokumentasi

📊 INFO & MONITORING:
  /stats               Statistik model & knowledge
  /system              Info CPU, RAM
  /time                Waktu sekarang
  /weather [kota]      Cuaca kota
  /tree [path]         Struktur folder
  /mode [mode]         Ganti/lihat mode pemrosesan

🤖 AUTO-LEARNING:
  /autotrain           Status auto-training
  /autotrain now       Jalankan training sekarang

💾 MANAGEMENT:
  /save                Simpan model & knowledge
  /watch               Status file watcher
  /reset               Reset model
  /clear               Bersihkan layar
  /exit                Keluar

🧠 MODE PEMROSESAN:
  thinking   - Deep analysis, architecture planning
  reasoning  - Logical step-by-step, debugging
  medium     - Balanced speed & quality (default)
  fast       - Quick response, simple answers

💡 TIPS:
  - Ketik bebas, sistem otomatis mengerti!
  - Model makin pintar seiring penggunaan
  - Auto-training berjalan di background
  - Training dari project Anda membuat model lebih akurat
"""

ERROR_NO_FILE = "File tidak ditemukan: {filepath}"
ERROR_NO_DIR = "Direktori tidak ditemukan: {directory}"
ERROR_NETWORK = "Gagal terhubung ke internet. Periksa koneksi Anda."
ERROR_PARSE = "Gagal mem-parsing kode: {error}"
ERROR_GENERIC = "Terjadi kesalahan: {error}"

SUCCESS_TRAIN = "Training selesai! {count} file diproses, {tokens} tokens dipelajari."
SUCCESS_SAVE = "Model dan knowledge base berhasil disimpan."
SUCCESS_LEARN = "Berhasil mempelajari {count} code snippets dari {source}."
SUCCESS_RESET = "Model berhasil di-reset ke keadaan awal."

STATUS_TRAINING = "Sedang training model dari {source}..."
STATUS_SEARCHING = "Mencari di internet: {query}..."
STATUS_SCRAPING = "Mengambil kode dari {url}..."
STATUS_WATCHING = "File watcher {status} untuk {path}"
STATUS_AUTO_TRAIN = "Auto-training selesai: {count} file diproses."

SUGGEST_HEADER = "💡 Suggestions ({count}):"
SUGGEST_ITEM = "  [{index}] {suggestion}  (confidence: {score:.1%})"
SUGGEST_EMPTY = "Belum ada suggestion. Coba:\n  - Training model dulu: /train <folder>\n  - Atau belajar dari internet: /search <query>"

LINE_SUGGEST_HEADER = "📝 Line Suggestions ({count}):"
LINE_SUGGEST_ITEM = "  [{index}] {suggestion}"

CONTEXT_TEMPLATE = """
[Language: {language}]
[File: {filename}]
[Line: {line_number}]
[Context]:
{context}
[Cursor]:
{current_line}
"""
