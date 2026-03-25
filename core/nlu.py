import re
from collections import Counter

# ===================================================================
# Indonesian NLP Libraries — all optional, graceful degradation
# ===================================================================
_stemmer = None          # PySastrawi stemmer
_lemmatizer = None       # nlp-id lemmatizer
_tokenizer = None        # IndoBERT tokenizer (transformers)
_nlp_ready = False


def _init_nlp():
    """
    Non-blocking NLP init. NEVER downloads models during startup.
    Priority: PySastrawi > nlp-id > built-in VERB_ROOT_MAP.
    """
    global _stemmer, _lemmatizer, _tokenizer, _nlp_ready
    if _nlp_ready:
        return

    # PySastrawi stemmer (fast, offline, pure Python — recommended)
    try:
        from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
        factory = StemmerFactory()
        _stemmer = factory.create_stemmer()
    except Exception:
        _stemmer = None

    # nlp-id lemmatizer (only if already downloaded — no auto-download)
    try:
        import importlib.util, sys, os
        if importlib.util.find_spec("nlp_id") is not None:
            # Guard: check model file exists before instantiating
            nlp_id_path = os.path.join(
                os.path.dirname(importlib.util.find_spec("nlp_id").origin),
                "lemmatizer"
            )
            if os.path.isdir(nlp_id_path):
                from nlp_id.lemmatizer import Lemmatizer
                _lemmatizer = Lemmatizer()
    except Exception:
        _lemmatizer = None

    # IndoBERT tokenizer — only if transformers installed AND model cached
    try:
        import transformers
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
        if os.path.isdir(cache_dir):
            # Only try if cached; do NOT download
            _tokenizer = transformers.AutoTokenizer.from_pretrained(
                "indobenchmark/indobert-base-p1",
                local_files_only=True,
            )
    except Exception:
        _tokenizer = None

    _nlp_ready = True


# === Comprehensive hardcoded Indonesian stopwords (no NLTK required) ===
_STOPWORDS_ID = {
    "dan", "di", "ke", "dari", "yang", "ini", "itu", "pada", "untuk",
    "dengan", "adalah", "oleh", "akan", "juga", "sudah", "belum", "atau",
    "saya", "aku", "kamu", "anda", "dia", "mereka", "kita", "kami",
    "bisa", "tidak", "ada", "tersebut", "dalam", "lagi", "telah", "saat",
    "harus", "punya", "seperti", "jadi", "mau", "ingin", "boleh", "perlu",
    "karena", "sebagai", "jika", "maka", "bahwa", "tetapi", "namun",
    "selain", "sehingga", "agar", "supaya", "walaupun", "meskipun",
    "setelah", "sebelum", "ketika", "hingga", "sampai", "sejak",
    "antara", "bagi", "tentang", "terhadap", "tanpa", "bukan", "jangan",
    "lebih", "sangat", "sekali", "saja", "pun", "pula", "lah", "tah",
    "nya", "kah", "lah", "kan", "me", "ber", "ter", "per", "ke", "se",
}


def lemmatize_text(text):
    """Stem/lemmatize Indonesian text. Uses PySastrawi > nlp-id > VERB_ROOT_MAP."""
    _init_nlp()
    if _stemmer:
        try:
            return _stemmer.stem(text)
        except Exception:
            pass
    if _lemmatizer:
        try:
            return _lemmatizer.lemmatize(text)
        except Exception:
            pass
    return text


def get_stopwords():
    """Get Indonesian stopwords (hardcoded — instant, no network)."""
    return _STOPWORDS_ID


def extract_keywords(text):
    """Extract meaningful keywords (remove stopwords)."""
    stops = _STOPWORDS_ID
    words = re.sub(r'[^\w\s]', '', text.lower()).split()
    return [w for w in words if w not in stops and len(w) > 1]


# === Indonesian verb root mapping ===
# Maps common prefixed/suffixed Indonesian verbs to their root action
VERB_ROOT_MAP = {
    # beri- family
    "berikan": "beri", "memberikan": "beri", "memberi": "beri", "diberi": "beri",
    "diberikan": "beri", "pemberian": "beri", "kasih": "beri", "kasihkan": "beri",
    # tulis- family
    "tuliskan": "tulis", "menuliskan": "tulis", "menulis": "tulis", "ditulis": "tulis",
    "dituliskan": "tulis", "penulisan": "tulis", "tulisan": "tulis",
    # isi- family
    "isikan": "isi", "mengisi": "isi", "mengisikan": "isi", "diisi": "isi",
    "diisikan": "isi", "pengisian": "isi", "isian": "isi",
    # tambah- family
    "tambahkan": "tambah", "menambahkan": "tambah", "menambah": "tambah",
    "ditambah": "tambah", "ditambahkan": "tambah", "penambahan": "tambah",
    # ubah- family
    "ubahkan": "ubah", "mengubah": "ubah", "diubah": "ubah", "perubahan": "ubah",
    # edit- family
    "mengedit": "edit", "diedit": "edit", "pengeditan": "edit",
    # buat- family
    "buatkan": "buat", "membuatkan": "buat", "membuat": "buat",
    "dibuatkan": "buat", "dibuat": "buat", "pembuatan": "buat",
    "bikin": "buat", "bikinkan": "buat", "membikin": "buat",
    # hapus- family
    "hapuskan": "hapus", "menghapus": "hapus", "menghapuskan": "hapus",
    "dihapus": "hapus", "penghapusan": "hapus",
    # baca- family
    "bacakan": "baca", "membaca": "baca", "dibaca": "baca",
    # cari- family
    "carikan": "cari", "mencari": "cari", "mencarikan": "cari",
    "dicari": "cari", "pencarian": "cari",
    # tampil- family
    "tampilkan": "tampil", "menampilkan": "tampil", "ditampilkan": "tampil",
    "perlihatkan": "tampil", "tunjukkan": "tampil", "tunjukin": "tampil",
    # perbaiki- family
    "memperbaiki": "perbaiki", "diperbaiki": "perbaiki", "perbaikan": "perbaiki",
    # perbarui- family
    "memperbarui": "perbarui", "diperbarui": "perbarui", "pembaruan": "perbarui",
    # pasang- family
    "pasangkan": "pasang", "memasang": "pasang", "dipasang": "pasang",
    # ganti- family
    "gantikan": "ganti", "mengganti": "ganti", "menggantikan": "ganti",
    "diganti": "ganti", "penggantian": "ganti",
    # lengkap- family
    "lengkapi": "lengkap", "melengkapi": "lengkap", "dilengkapi": "lengkap",
    # sisip- family
    "sisipkan": "sisip", "menyisipkan": "sisip", "disisipkan": "sisip",
    # masuk- family
    "masukkan": "masuk", "memasukkan": "masuk", "dimasukkan": "masuk",
    # simpan- family
    "simpankan": "simpan", "menyimpan": "simpan", "disimpan": "simpan",
    # jelaskan- family
    "jelaskan": "jelas", "menjelaskan": "jelas", "dijelaskan": "jelas",
    "jelasin": "jelas",
    # jalankan- family
    "jalankan": "jalan", "menjalankan": "jalan", "dijalankan": "jalan",
    # unduh/download - family
    "unduh": "download", "mengunduh": "download", "diunduh": "download",
    "unduhkan": "download", "scarica": "download",
    # cari/research - family
    "riset": "research", "teliti": "research", "pelajari": "research",
    "analisa": "research", "analisis": "research", "investigasi": "research",
}


def normalize_verbs(words):
    """Normalize Indonesian verbs to their root forms."""
    result = []
    for w in words:
        root = VERB_ROOT_MAP.get(w, w)
        result.append(root)
    return result


class NLUEngine:

    # =========================================================
    # Intent keywords now use ROOT FORMS of Indonesian verbs
    # This allows "berikan", "memberikan", "kasih" etc. to all
    # match the root "beri" after normalization.
    # =========================================================
    INTENT_KEYWORDS = {
        "create_file": {
            "id": ["buat", "buat file", "buat kode", "generate",
                   "create", "buat baru", "file baru"],
            "en": ["create", "make", "generate", "add", "new", "build", "write",
                   "scaffold", "init", "setup", "create file"],
        },
        "create_project": {
            "id": ["buat project", "buat proyek", "buat aplikasi", "buat app",
                   "setup project", "init project"],
            "en": ["create project", "new project", "build project", "init project",
                   "setup project", "scaffold project", "create app", "new app"],
        },
        "read_file": {
            "id": ["baca", "tampil", "buka", "cek",
                   "show", "display", "lihat file", "baca file"],
            "en": ["read", "show", "display", "view", "open", "cat", "print",
                   "see", "look", "check", "inspect"],
        },
        "edit_file": {
            "id": ["edit", "ubah", "ganti", "modifikasi", "perbaiki", "update",
                   "perbarui", "revisi", "refactor",
                   "edit file", "ubah file", "perbarui file", "edit isi",
                   "tambah pada", "sisip di", "tambah di",
                   "tulis", "isi", "tambah", "pasang", "lengkap",
                   "sisip", "masuk", "taruh", "terapkan"],
            "en": ["edit", "modify", "change", "update", "fix", "alter",
                   "replace", "refactor", "revise", "patch", "amend",
                   "edit file", "modify file", "update file",
                   "add", "insert", "put", "fill", "write", "set", "apply"],
        },
        "delete_file": {
            "id": ["hapus", "delete", "buang", "hilangkan", "remove",
                   "bersihkan", "singkirkan"],
            "en": ["delete", "remove", "erase", "destroy", "clean", "purge",
                   "clear", "wipe", "drop", "unlink"],
        },
        "explain_code": {
            "id": ["jelas", "apa itu", "apa maksud", "artikan",
                   "beritahu", "kasih tau", "kenapa", "mengapa", "gimana cara",
                   "bagaimana", "cara kerja", "fungsi dari", "kegunaan"],
            "en": ["explain", "what is", "what does", "how does", "describe",
                   "tell me", "why", "how to", "what's", "meaning of",
                   "purpose of", "how it works"],
        },
        "debug_code": {
            "id": ["debug", "error", "bug", "gagal", "tidak bisa", "tidak jalan",
                   "masalah", "salah", "fix", "kenapa error",
                   "ga bisa", "gak bisa", "nggak bisa", "ga jalan", "rusak"],
            "en": ["debug", "error", "bug", "fix", "broken", "not working",
                   "issue", "problem", "wrong", "fail", "crash", "exception",
                   "traceback", "stacktrace"],
        },
        "search_code": {
            "id": ["cari kode", "cari contoh", "cari script", "cari program",
                   "cari snippet", "cari algoritma"],
            "en": ["search code", "find code", "code lookup", "snippet search"],
        },
        "search_web": {
            "id": ["berita", "informasi", "info tentang", "siapa", "dimana",
                   "kapan", "apa itu", "cari tentang", "berita tentang", "artikel",
                   "beri berita", "kasih info", "beri informasi", "cari informasi",
                   "search", "cari", "temukan", "find"],
            "en": ["news", "information", "info about", "who is", "where is",
                   "when", "what is", "search about", "read about", "article",
                   "search", "find", "look up", "google", "query"],
        },
        "learn_url": {
            "id": ["pelajari", "belajar dari", "ambil dari", "scrape",
                   "ambil kode dari", "pelajari url", "belajar url"],
            "en": ["learn from", "scrape", "fetch from", "get from",
                   "study", "absorb", "learn url", "crawl"],
        },
        "suggest_code": {
            "id": ["suggest", "sarankan", "saran", "rekomendasikan", "autocomplete",
                   "complete", "lanjutkan", "teruskan kode"],
            "en": ["suggest", "recommend", "autocomplete", "complete",
                   "continue", "finish", "predict", "what comes next"],
        },
        "train_model": {
            "id": ["train", "latih", "training", "latihan", "pelajari folder",
                   "scan folder", "belajar dari folder"],
            "en": ["train", "learn", "training", "study folder", "scan",
                   "process", "analyze folder", "index"],
        },
        "show_stats": {
            "id": ["statistik", "stats", "status",
                   "berapa", "jumlah", "seberapa"],
            "en": ["stats", "statistics", "status", "info", "information",
                   "how many", "count", "metrics", "dashboard"],
        },
        "show_time": {
            "id": ["jam berapa", "waktu", "tanggal", "hari ini", "sekarang jam",
                   "hari apa", "tanggal berapa"],
            "en": ["time", "date", "today", "now", "what time",
                   "what day", "current time", "clock"],
        },
        "show_weather": {
            "id": ["cuaca", "weather", "hujan", "panas", "suhu", "temperatur",
                   "cuaca hari ini"],
            "en": ["weather", "temperature", "rain", "sunny", "forecast",
                   "climate", "hot", "cold"],
        },
        "system_info": {
            "id": ["sistem", "system", "cpu", "ram", "memory", "memori",
                   "spek", "spesifikasi", "performa"],
            "en": ["system", "cpu", "ram", "memory", "performance",
                   "specs", "hardware", "resource", "usage"],
        },
        "greeting": {
            "id": ["halo", "hai", "hi", "hey", "selamat pagi", "selamat siang",
                   "selamat malam", "apa kabar", "assalamualaikum", "salam"],
            "en": ["hello", "hi", "hey", "good morning", "good afternoon",
                   "good evening", "how are you", "greetings", "sup", "yo"],
        },
        "farewell": {
            "id": ["bye", "dadah", "sampai jumpa", "pamit", "keluar",
                   "selesai", "exit", "quit", "stop"],
            "en": ["bye", "goodbye", "exit", "quit", "see you", "farewell",
                   "done", "stop", "leave", "end"],
        },
        "help": {
            "id": ["bantuan", "tolong", "bantu", "help", "gimana", "cara",
                   "bagaimana", "petunjuk", "panduan", "tutorial"],
            "en": ["help", "assist", "guide", "how", "instruction",
                   "manual", "documentation", "docs", "tutorial"],
        },
        "save": {
            "id": ["simpan", "save", "backup", "export"],
            "en": ["save", "store", "backup", "export", "persist"],
        },
        "list_files": {
            "id": ["daftar file", "list file", "file apa saja", "struktur folder",
                   "tree", "direktori", "tampil folder"],
            "en": ["list files", "directory", "tree", "folder content",
                   "structure", "ls", "dir"],
        },
        "run_command": {
            "id": ["jalan", "eksekusi", "buka cmd", "jalan cmd", "run",
                   "terminal", "eksekusi perintah", "jalan terminal"],
            "en": ["run command", "execute", "run", "cmd", "terminal", "start"],
        },
        "download_file": {
            "id": ["download", "unduh", "scarica", "ambil file", "simpan dari",
                   "download file", "unduh file", "tarik file"],
            "en": ["download", "fetch file", "get file", "save file from",
                   "pull", "wget", "curl"],
        },
        "read_news": {
            "id": ["berita", "baca berita", "cari berita", "berita terbaru",
                   "news", "artikel berita", "headline", "terkini",
                   "kabar", "informasi berita"],
            "en": ["news", "latest news", "read news", "headlines", "article",
                   "breaking news", "today news"],
        },
        "research_topic": {
            "id": ["research", "riset", "pelajari", "analisa", "investigasi",
                   "telusuri", "cari tahu tentang", "informasi lengkap",
                   "jelaskan tentang", "teknologi"],
            "en": ["research", "study", "investigate", "analyze", "learn about",
                   "deep dive", "explore", "comprehensive info about"],
        },
        "generate_code": {
            "id": ["buat kode", "generate kode", "tulis kode",
                   "kode untuk", "coding", "buat fungsi", "buat class",
                   "buat program", "buat script"],
            "en": ["generate code", "write code", "code for", "implement",
                   "create function", "create class", "write program",
                   "write script", "code this", "implement this"],
        },
    }

    ENTITY_PATTERNS = {
        "filepath": [
            r'(?:file|berkas)\s+["\']?([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+)["\']?',
            r'["\']([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+)["\']',
            r'(?:di|in|dari|from|ke|to)\s+([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+)',
            r'\b([a-zA-Z0-9_-]+\.(?:py|js|ts|html|css|java|cpp|go|rs|php|rb|json|yaml|yml|md|txt|sql|sh|bat))\b',
        ],
        "url": [
            r'(https?://[^\s]+)',
        ],
        "language": [
            r'\b(python|javascript|typescript|java|cpp|c\+\+|go|rust|php|ruby|'
            r'swift|kotlin|dart|sql|html|css|bash|shell|react|vue|angular|'
            r'node\.?js|express|flask|django|fastapi|laravel|tailwind)\b',
        ],
        "number": [
            r'\b(\d+)\b',
        ],
        "code_element": [
            r'\b(function|fungsi|class|kelas|variable|variabel|method|metode|'
            r'loop|perulangan|condition|kondisi|array|list|dictionary|dict|'
            r'string|integer|float|boolean|import|module|modul|package|paket)\b',
        ],
        "city": [
            r'(?:cuaca|weather|di|in|kota|city)\s+([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)',
        ],
    }

    RESPONSE_HINTS = {
        "greeting": "Sapa balik user dengan ramah, tanyakan apa yang bisa dibantu.",
        "create_file": "User ingin membuat file baru. Tanyakan detail jika kurang.",
        "edit_file": "User ingin mengedit file. Identifikasi file dan perubahan.",
        "explain_code": "User ingin penjelasan. Berikan penjelasan detail.",
        "debug_code": "User punya masalah kode. Bantu debug dan perbaiki.",
        "search_code": "User ingin cari kode. Lakukan pencarian internet.",
        "suggest_code": "User ingin suggestion. Berikan autocomplete.",
    }

    def __init__(self):
        self.conversation_history = []
        self.context = {}
        self._compile_patterns()

    def _compile_patterns(self):
        self.compiled_entity_patterns = {}
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            self.compiled_entity_patterns[entity_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def understand(self, user_input):
        if not user_input or not user_input.strip():
            return self._empty_result()

        cleaned = user_input.strip()
        lowered = cleaned.lower()

        input_language = self._detect_language(lowered)
        intent, confidence = self._classify_intent(lowered)
        entities = self._extract_entities(cleaned)
        mode_suggestion = self._suggest_mode(intent, cleaned, entities)

        result = {
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "language": input_language,
            "response_hint": self.RESPONSE_HINTS.get(intent, ""),
            "original_input": cleaned,
            "mode_suggestion": mode_suggestion,
            "is_question": self._is_question(lowered),
            "is_code": self._is_code_input(cleaned),
            "sentiment": self._detect_sentiment(lowered),
        }

        self.conversation_history.append(result)
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

        return result

    def _classify_intent(self, text):
        scores = Counter()
        raw_words = text.split()

        # Step 1: Normalize verbs to root forms
        normalized_words = normalize_verbs(raw_words)
        normalized_text = " ".join(normalized_words)
        words = set(normalized_words)

        for intent_name, lang_keywords in self.INTENT_KEYWORDS.items():
            for lang, keywords in lang_keywords.items():
                for keyword in keywords:
                    kw_lower = keyword.lower()
                    kw_words = set(kw_lower.split())

                    # Exact substring match on normalized text
                    if kw_lower in normalized_text:
                        word_count = len(kw_words)
                        scores[intent_name] += word_count * 2
                        if normalized_text.startswith(kw_lower):
                            scores[intent_name] += 3
                        if normalized_text == kw_lower:
                            scores[intent_name] += 5
                    else:
                        # Fuzzy semantic matching (Jaccard-like overlap)
                        overlap = kw_words.intersection(words)
                        if len(overlap) > 0 and len(overlap) >= len(kw_words) * 0.6:
                            scores[intent_name] += len(overlap)

        # ========================================
        # File-entity aware fallback
        # ========================================
        has_file = bool(re.search(
            r'\b[\w-]+\.(?:py|js|ts|html|css|java|txt|json|md|xml|yaml|yml)\b', text
        ))
        file_action_roots = {
            "beri", "tulis", "isi", "tambah", "pasang", "taruh", "ubah",
            "ganti", "edit", "perbarui", "lengkap", "sisip", "masuk",
            "add", "put", "fill", "write", "insert", "set", "apply",
        }

        # ========================================
        # CRITICAL: Informational context override
        # If no file detected AND text contains informational
        # words, FORCE to search_web or read_news
        # ========================================
        informational_words = {
            "artikel", "tentang", "informasi", "info", "berita",
            "kabar", "news", "terkini", "terbaru", "headline",
            "topik", "riset", "research", "pelajari", "telusuri",
        }
        has_info_context = bool(informational_words.intersection(set(text.split())))

        if not has_file and has_info_context:
            # Check if news-related
            news_words = {"berita", "news", "terkini", "terbaru", "headline", "kabar"}
            if news_words.intersection(set(text.split())):
                return ("read_news", 0.75)
            # Check if research-related
            research_words = {"riset", "research", "pelajari", "telusuri", "analisa"}
            if research_words.intersection(words):
                return ("research_topic", 0.7)
            # Default: general web search
            return ("search_web", 0.7)

        if not scores:
            if has_file:
                if file_action_roots.intersection(words):
                    return ("edit_file", 0.6)
                return ("read_file", 0.5)
            if self._is_code_input(text):
                return ("suggest_code", 0.6)
            return ("unknown", 0.0)

        best_intent = scores.most_common(1)[0]
        intent_name = best_intent[0]
        raw_score = best_intent[1]

        max_possible = 15
        confidence = min(raw_score / max_possible, 1.0)

        # ========================================
        # Post-scoring override: file-less edit → redirect
        # If edit_file wins but NO file entity and HAS info words → redirect
        # ========================================
        if intent_name == "edit_file" and not has_file:
            # Check: is this really about editing, or about search/info?
            if has_info_context:
                news_words = {"berita", "news", "terkini", "terbaru", "headline", "kabar"}
                if news_words.intersection(set(text.split())):
                    return ("read_news", 0.75)
                return ("search_web", 0.7)
            # If top score for edit_file is very low and no file, fallback
            if confidence < 0.4:
                return ("search_web", 0.5)

        # Override: if file detected + low confidence + non-file intent, redirect
        if has_file and confidence < 0.5:
            file_intents = {"create_file", "edit_file", "read_file", "delete_file"}
            if intent_name not in file_intents:
                for fi in file_intents:
                    if fi in scores:
                        return (fi, max(confidence, 0.5))
                if file_action_roots.intersection(words):
                    return ("edit_file", 0.6)
                return ("read_file", 0.5)

        # Disambiguation: if edit_file and search_web both scored,
        # prefer based on file presence
        if "edit_file" in scores and "search_web" in scores:
            if has_file:
                return ("edit_file", max(confidence, 0.6))
            else:
                if scores["search_web"] >= scores["edit_file"]:
                    return ("search_web", confidence)

        return (intent_name, confidence)

    def _extract_entities(self, text):
        entities = {}

        for entity_type, patterns in self.compiled_entity_patterns.items():
            matches = []
            for pattern in patterns:
                found = pattern.findall(text)
                matches.extend(found)

            if matches:
                entities[entity_type] = list(dict.fromkeys(matches))

        return entities

    def _detect_language(self, text):
        id_words = {
            "buat", "bikin", "cari", "hapus", "ubah", "tolong", "apa",
            "bagaimana", "gimana", "kenapa", "mengapa", "dari", "untuk",
            "yang", "ini", "itu", "dengan", "dan", "atau", "silahkan",
            "mohon", "bisa", "mau", "ingin", "hendak", "boleh", "perlu",
            "tidak", "bukan", "jangan", "belum", "sudah", "sedang",
            "halo", "hai", "selamat", "terima kasih", "makasih",
            "ke", "di", "pada", "oleh", "saya", "aku", "kamu", "anda",
        }

        words = set(text.lower().split())
        id_count = len(words & id_words)

        if id_count >= 2 or (id_count >= 1 and len(words) <= 5):
            return "id"
        return "en"

    def _suggest_mode(self, intent, text, entities):
        thinking_triggers = ["arsitektur", "architecture", "design pattern",
                           "rancang", "rencanakan", "plan", "strategi",
                           "buat project", "create project", "build system"]
        for trigger in thinking_triggers:
            if trigger in text.lower():
                return "thinking"

        if intent in ("debug_code", "explain_code"):
            return "reasoning"

        if intent in ("greeting", "farewell", "show_time", "show_weather",
                      "system_info", "help", "save"):
            return "fast"

        return "medium"

    def _is_question(self, text):
        question_markers = [
            "?", "apa", "siapa", "dimana", "kapan", "kenapa", "mengapa",
            "bagaimana", "gimana", "berapa", "mana", "apa itu",
            "what", "who", "where", "when", "why", "how", "which",
            "can", "could", "would", "should", "is", "are", "do", "does",
        ]
        for marker in question_markers:
            if marker in text:
                return True
        return False

    def _is_code_input(self, text):
        code_indicators = [
            "def ", "class ", "import ", "from ", "function ",
            "var ", "let ", "const ", "if(", "for(", "while(",
            "=>", "->", "::", "==", "!=", ">=", "<=",
            "self.", "this.", "console.", "print(",
            "{", "}", "()", "[]",
        ]
        indicator_count = sum(1 for ind in code_indicators if ind in text)
        symbol_ratio = sum(1 for c in text if c in "=(){}[];:<>+-*/&|!@#$%^~") / max(len(text), 1)
        return indicator_count >= 1 or symbol_ratio > 0.15

    def _detect_sentiment(self, text):
        positive = {"bagus", "keren", "hebat", "mantap", "good", "great",
                   "awesome", "nice", "perfect", "excellent", "terima kasih",
                   "makasih", "thanks", "thank", "love", "suka"}
        negative = {"jelek", "buruk", "gagal", "error", "rusak", "bad",
                   "wrong", "terrible", "hate", "benci", "kesal",
                   "lambat", "slow", "broken", "fail"}

        words = set(text.split())
        pos = len(words & positive)
        neg = len(words & negative)

        if pos > neg:
            return "positive"
        elif neg > pos:
            return "negative"
        return "neutral"

    def _empty_result(self):
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "entities": {},
            "language": "id",
            "response_hint": "",
            "original_input": "",
            "mode_suggestion": "fast",
            "is_question": False,
            "is_code": False,
            "sentiment": "neutral",
        }

    def get_context(self):
        if not self.conversation_history:
            return {}

        recent = self.conversation_history[-5:]
        return {
            "recent_intents": [r["intent"] for r in recent],
            "recent_entities": [r["entities"] for r in recent],
            "turn_count": len(self.conversation_history),
            "dominant_language": self._get_dominant_language(),
        }

    def _get_dominant_language(self):
        if not self.conversation_history:
            return "id"

        langs = [r["language"] for r in self.conversation_history]
        return max(set(langs), key=langs.count)

    def reset(self):
        self.conversation_history = []
        self.context = {}
