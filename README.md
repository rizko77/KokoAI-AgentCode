# KokoAI AgentCode v2.1

**KokoAI** adalah asisten coding AI lokal berbasis Python yang berjalan sepenuhnya di komputer Anda — tanpa API berbayar wajib, tanpa cloud, dan tetap bisa dipakai saat koneksi lemot.

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![NLP](https://img.shields.io/badge/NLP-PySastrawi%20%7C%20IndoBERT-orange)](https://github.com/har07/PySastrawi)

---

## Fitur Utama

| Fitur | Keterangan |
|-------|------------|
| **NLU Bahasa Indonesia** | Memahami perintah natural dalam Bahasa Indonesia |
| **Auto Code-Complete** | Hybrid N-gram local + Gemini/Claude jika ada API |
| **Pembaca Berita** | Google News RSS, Wikipedia, real-time |
| **Web Search** | Google Search sebagai primary engine |
| **Tech Research** | Riset topik mendalam dengan AI |
| **Download File** | Download file dari URL ke workspace |
| **File Manager** | Buat, edit, baca, hapus file di workspace |
| **Slow-Net Friendly** | Retry otomatis, timeout adaptif, kompresi |
| **GUI Tkinter** | Antarmuka grafis dark-theme modern |
| **Multi AI Provider** | Gemini 2.0 Flash, Claude Sonnet, OpenAI GPT-4o |

---

## Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/username/kokoai-agentcode.git
cd kokoai-agentcode

# Buat virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Konfigurasi (Opsional)
```bash
# Salin template config
copy .env.sample .env

# Edit .env dan isi API key jika ingin pakai AI cloud:
# GEMINI_API_KEY=your_key_here
# CLAUDE_API_KEY=your_key_here
```

### 3. Jalankan

**Mode CLI:**
```bash
python main.py
```

**Mode GUI (Tkinter):**
```bash
python gui.py
```

---

## NLP Indonesia

KokoAI menggunakan stack NLP berlapis untuk memahami Bahasa Indonesia:

| Library | Fungsi | Status |
|---------|--------|--------|
| **PySastrawi** | Stemmer (wajib, offline) | ✅ Termasuk di requirements |
| **VERB_ROOT_MAP** | 100+ normalisasi kata kerja | ✅ Built-in |
| **IndoBERT** | Deep NLU (opsional) | Manual install |
| **nlp-id** | Lemmatizer (opsional) | Manual install |

### Install NLP Opsional
```bash
# IndoBERT (butuh ~500MB, opsionaluntuk akurasi lebih tinggi)
pip install transformers torch
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('indobenchmark/indobert-base-p1')"

# nlp-id (butuh download model ~282MB)
pip install nlp-id

# NLTK
pip install nltk
python -m nltk.downloader stopwords punkt
```

---

## AI Provider Support

KokoAI mendukung multiple AI provider. Isi API key di `.env`:

```env
# Primary (direkomendasikan)
GEMINI_API_KEY=your_gemini_key   # Google AI Studio: aistudio.google.com

# Alternatif
CLAUDE_API_KEY=your_claude_key   # Anthropic: console.anthropic.com
OPENAI_API_KEY=your_openai_key   # OpenAI: platform.openai.com

# Urutan prioritas
AI_PROVIDER_PRIORITY=gemini,claude,openai,local
```

Tanpa API key → KokoAI tetap berjalan menggunakan **local N-gram brain**.

---

## Contoh Perintah

```
KokoAI> buat file index.html untuk landing page jam tangan pakai tailwind css
KokoAI> edit file index.html tambahkan hero section yang profesional
KokoAI> berikan 1 artikel tentang teknologi AI terbaru
KokoAI> cari berita terkini tentang pemrograman
KokoAI> riset tentang quantum computing
KokoAI> download https://example.com/dataset.csv
KokoAI> tampilkan isi file index.html
KokoAI> lihat statistik sistem
```

---

## Struktur Project

```
kokoai-agentcode/
├── main.py              # CLI entry point
├── gui.py               # GUI Tkinter entry point
├── requirements.txt     # Dependencies
├── .env.sample          # Template konfigurasi
├── .gitignore
├── core/
│   ├── engine.py        # Main orchestrator
│   ├── nlu.py           # NLU + PySastrawi + IndoBERT
│   ├── brain.py         # N-gram / Markov Chain local brain
│   ├── autocomplete_code.py  # Hybrid autocomplete
│   └── thinking.py      # Mode berpikir AI
├── api/
│   ├── router.py        # AI provider router
│   ├── gemini-api/      # Google Gemini client
│   ├── claude-api/      # Anthropic Claude client
│   └── openai-api/      # OpenAI client
├── tool/
│   ├── internet_search.py    # Google Search + News + Wikipedia
│   ├── web_scraping.py       # Scrapy deep crawler
│   └── ...
├── config/
│   └── settings.py      # Konfigurasi global
├── workspace/           # Tempat file hasil generate AI
└── data/                # Knowledge base lokal
```

---

## Keamanan

- Semua terminal command memerlukan konfirmasi manual
- Web scraping memfilter konten berbahaya (SQL injection, `rm -rf`, dll)
- API key tersimpan di `.env` (TIDAK ikut ke git)

---

## Lisensi

MIT License — bebas digunakan, dimodifikasi, dan didistribusikan.

---

**Dibuat oleh Rizko Imsar | KokoDev Studio 🇮🇩**
