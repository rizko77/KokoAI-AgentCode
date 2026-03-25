import os
import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config.settings import (
    WORKSPACE_DIR, DATA_DIR, NGRAM_SIZE, MAX_SUGGESTIONS,
    TRAINING_INTERVAL, AUTO_LEARN, AUTO_SCHEDULER,
    SUPPORTED_EXTENSIONS, KNOWLEDGE_FILE, MODEL_STATE_FILE,
    TRAINING_LOG_FILE, CONVERSATION_FILE, APP_NAME, VERSION,
)
from core.tokenizer import CodeTokenizer
from core.knowledge import KnowledgeBase
from core.brain import AIBrain
from core.nlu import NLUEngine
from core.thinking import ThinkingMode
from core.conversation import ConversationMemory
from core.code_generator import CodeGenerator
from core.scheduler import TrainingScheduler


class FileChangeHandler(FileSystemEventHandler):

    def __init__(self, engine):
        self.engine = engine
        self.last_event_time = 0
        self.debounce_seconds = 2

    def on_modified(self, event):
        if event.is_directory:
            return
        now = time.time()
        if now - self.last_event_time < self.debounce_seconds:
            return
        self.last_event_time = now

        filepath = Path(event.src_path)
        if filepath.suffix.lower() in SUPPORTED_EXTENSIONS:
            self.engine._on_file_changed(filepath)

    def on_created(self, event):
        if event.is_directory:
            return
        filepath = Path(event.src_path)
        if filepath.suffix.lower() in SUPPORTED_EXTENSIONS:
            self.engine._on_file_changed(filepath)


class CoreEngine:

    def __init__(self):
        self.tokenizer = CodeTokenizer()
        self.knowledge = KnowledgeBase(KNOWLEDGE_FILE)
        self.brain = AIBrain(
            tokenizer=self.tokenizer,
            knowledge_base=self.knowledge,
            model_path=MODEL_STATE_FILE,
            ngram_size=NGRAM_SIZE,
        )
        self.nlu = NLUEngine()
        self.thinking = ThinkingMode()
        self.memory = ConversationMemory(save_path=CONVERSATION_FILE)
        self.code_gen = CodeGenerator(WORKSPACE_DIR)
        self.scheduler = TrainingScheduler(
            engine=self,
            interval_minutes=TRAINING_INTERVAL,
            log_path=TRAINING_LOG_FILE,
        )

        self.is_running = False
        self.observer = None
        self.training_thread = None
        self.watched_files = {}
        self.current_file = None
        self.current_language = "python"

        self.on_suggestion_ready = None
        self.on_training_complete = None
        self.on_error = None

        # Lazy-loaded: AI Router (Gemini/Claude/OpenAI)
        self._ai_router = None
        # Lazy-loaded: Autocomplete engine
        self._autocomplete = None

    def start(self):
        self.is_running = True
        self._initial_training()
        self._start_file_watcher()

        if AUTO_LEARN:
            self._start_auto_training()

        if AUTO_SCHEDULER:
            self.scheduler.start()

    def stop(self):
        self.is_running = False

        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)

        self.scheduler.stop()
        self.brain.save_model()
        self.knowledge.save()
        self.memory.save()

    def process_input(self, user_input):
        nlu_result = self.nlu.understand(user_input)
        self.thinking.auto_select_mode(nlu_result)
        self.memory.add_user(
            user_input,
            intent=nlu_result.get("intent"),
            entities=nlu_result.get("entities"),
        )

        intent = nlu_result.get("intent", "unknown")
        entities = nlu_result.get("entities", {})
        mode = self.thinking.current_mode

        response = self._handle_intent(intent, user_input, entities, nlu_result)
        self.memory.add_assistant(
            response.get("text", ""),
            mode=mode,
            action=intent,
        )

        response["mode"] = self.thinking.get_mode_name()
        response["intent"] = intent
        response["confidence"] = nlu_result.get("confidence", 0)

        return response

    def _handle_intent(self, intent, user_input, entities, nlu_result):
        handlers = {
            "greeting": self._intent_greeting,
            "farewell": self._intent_farewell,
            "help": self._intent_help,
            "create_file": self._intent_create_file,
            "create_project": self._intent_create_project,
            "read_file": self._intent_read_file,
            "edit_file": self._intent_edit_file,
            "delete_file": self._intent_delete_file,
            "explain_code": self._intent_explain,
            "debug_code": self._intent_debug,
            "search_code": self._intent_search,
            "search_web": self._intent_search_web,
            "learn_url": self._intent_learn,
            "suggest_code": self._intent_suggest,
            "generate_code": self._intent_generate,
            "train_model": self._intent_train,
            "show_stats": self._intent_stats,
            "show_time": self._intent_time,
            "show_weather": self._intent_weather,
            "system_info": self._intent_system,
            "save": self._intent_save,
            "list_files": self._intent_list_files,
            "run_command": self._intent_run_command,
            "download_file": self._intent_download_file,
            "read_news": self._intent_read_news,
            "research_topic": self._intent_research_topic,
        }

        handler = handlers.get(intent)
        if handler:
            return handler(user_input, entities, nlu_result)

        if nlu_result.get("is_code"):
            return self._intent_suggest(user_input, entities, nlu_result)

        # Last resort: try AI router for unknown queries
        router = self._get_ai_router()
        if router and router.get_primary_provider() != "local":
            answer, provider = router.answer(user_input)
            if answer and len(answer) > 20:
                return {"text": answer, "type": "ai", "provider": provider}

        return self._intent_unknown(user_input, entities, nlu_result)

    def _get_ai_router(self):
        """Lazy-load AI router."""
        if self._ai_router is None:
            try:
                import sys, os
                sys.path.insert(0, str(WORKSPACE_DIR.parent))
                from api.router import get_router
                self._ai_router = get_router()
            except Exception:
                self._ai_router = False
        return self._ai_router if self._ai_router else None

    def _get_autocomplete(self):
        """Lazy-load autocomplete engine."""
        if self._autocomplete is None:
            try:
                from core.autocomplete_code import AutocompleteEngine
                self._autocomplete = AutocompleteEngine(
                    brain=self.brain,
                    knowledge_base=self.knowledge,
                )
            except Exception:
                self._autocomplete = False
        return self._autocomplete if self._autocomplete else None

    def _intent_greeting(self, text, entities, nlu):
        from tool.time_date_today import get_now
        greetings = [
            "Hai! Senang bertemmu denganmu",
            "Halo! Siap membantu coding mu hari ini",
            "Hey! Ada yang bisa kubantu?",
        ]
        import random
        greeting = random.choice(greetings)
        return {"text": f"{greeting}! Sekarang {get_now()}. Ketik apapun, aku siap bantu!", "type": "greeting"}

    def _intent_farewell(self, text, entities, nlu):
        return {"text": "Sampai jumpa! Semoga coding-mu lancar!", "type": "farewell", "exit": True}

    def _intent_help(self, text, entities, nlu):
        from prompt.static import HELP_MESSAGE
        return {"text": HELP_MESSAGE, "type": "help"}

    def _intent_create_file(self, text, entities, nlu):
        files = entities.get("filepath", [])
        if not files:
            return {"text": "Mau buat file apa? Sebutkan nama file-nya (contoh: main.py)", "type": "ask"}

        filename = files[0]
        language = entities.get("language", ["python"])[0] if "language" in entities else None

        content = self._generate_file_content(filename, text, language)
        result = self.code_gen.create_file(filename, content)

        if result["success"]:
            return {"text": f"File berhasil dibuat: {result['path']}", "type": "success", "data": result}
        return {"text": f"Gagal membuat file: {result['error']}", "type": "error"}

    def _intent_create_project(self, text, entities, nlu):
        words = text.lower().split()
        project_name = None
        project_type = "python"

        for word in words:
            if word not in ("buat", "bikin", "buatkan", "project", "proyek", "create", "new",
                           "setup", "init", "aplikasi", "app", "web", "flask", "node", "python"):
                if len(word) > 2:
                    project_name = word
                    break

        if not project_name:
            project_name = "project_baru"

        for ptype in ("flask", "web", "node", "python"):
            if ptype in text.lower():
                project_type = ptype
                break

        result = self.code_gen.create_project(project_name, project_type)
        if result["success"]:
            files = ", ".join(result["files_created"])
            return {"text": f"Project '{project_name}' berhasil dibuat di {result['path']}!\nFile: {files}", "type": "success", "data": result}
        return {"text": f"Gagal membuat project: {result['error']}", "type": "error"}

    def _intent_read_file(self, text, entities, nlu):
        files = entities.get("filepath", [])
        if not files:
            last_file = self.memory.get_last_file()
            if last_file:
                files = [last_file]
            else:
                return {"text": "File mana yang mau dibaca? Sebutkan nama file-nya.", "type": "ask"}

        result = self.code_gen.read_file(files[0])
        if result["success"]:
            content = result["content"]
            if len(content) > 3000:
                content = content[:3000] + "\n... (dipotong)"
            return {"text": f"📄 {result['path']} ({result['lines']} baris, {result['language']}):\n\n{content}", "type": "file_content", "data": result}
        return {"text": f"Gagal membaca: {result['error']}", "type": "error"}

    def _intent_edit_file(self, text, entities, nlu):
        files = entities.get("filepath", [])
        if not files:
            last_file = self.memory.get_last_file()
            if last_file:
                files = [last_file]
            else:
                return {"text": "File mana yang mau diedit? Sebutkan nama file-nya.", "type": "ask"}

        file_path = files[0]
        read_res = self.code_gen.read_file(file_path)
        if not read_res["success"]:
            return {"text": f"Gagal membaca {file_path}: {read_res['error']}", "type": "error"}

        content = read_res["content"]
        ext = Path(file_path).suffix.lower()
        text_lower = text.lower()

        # === Handle non-code text files (.txt, .md, .csv) ===
        if ext in (".txt", ".md", ".csv"):
            new_lines = self._generate_text_content(text_lower, file_path)
            if new_lines:
                merged = content.strip() + "\n" + new_lines if content.strip() else new_lines
                self.code_gen._resolve_path(file_path).write_text(merged, encoding="utf-8")
                return {"text": f"Berhasil memperbarui isi {file_path}.", "type": "success"}

        # === Handle color/theme changes ===
        if "warna" in text_lower or "color" in text_lower or "tema" in text_lower:
            import re
            color_matches = re.findall(r'(biru|merah|hijau|hitam|putih|kuning|ungu|orange|pink|blue|red|green|black|white|yellow|purple)', text_lower)
            if color_matches:
                color = color_matches[0]
                color_map = {
                    "biru": "#3b82f6", "merah": "#ef4444", "hijau": "#22c55e",
                    "kuning": "#eab308", "ungu": "#a855f7", "hitam": "#1f2937",
                    "orange": "#f97316", "pink": "#ec4899", "putih": "#ffffff",
                }
                hex_col = color_map.get(color, color)
                new_content = re.sub(r'#[0-9a-fA-F]{6}', hex_col, content, count=5)
                new_content = re.sub(r'bg-\w+-500', f'bg-{color}-500', new_content)
                new_content = re.sub(r'from-\w+-500', f'from-{color}-500', new_content)
                new_content = re.sub(r'to-\w+-600', f'to-{color}-600', new_content)
                self.code_gen._resolve_path(file_path).write_text(new_content, encoding="utf-8")
                return {"text": f"Berhasil mengubah tema warna {file_path} menjadi {color}.", "type": "success"}

        # === Handle HTML section injection (footer, header, hero, navbar) ===
        if ext in (".html", ".htm"):
            section = self._detect_html_section(text_lower)
            if section:
                new_content = self._inject_html_section(content, section, text_lower)
                self.code_gen._resolve_path(file_path).write_text(new_content, encoding="utf-8")
                return {"text": f"Berhasil menambahkan {section} pada {file_path}.", "type": "success"}
            # Full regenerate as fallback
            new_content = self._generate_file_content(file_path, text, "html")
            self.code_gen._resolve_path(file_path).write_text(new_content, encoding="utf-8")
            return {"text": f"Berhasil memperbarui isi {file_path}.", "type": "success"}

        # === Generic file: regenerate ===
        new_content = self._generate_file_content(file_path, text, ext.replace(".", ""))
        self.code_gen._resolve_path(file_path).write_text(new_content, encoding="utf-8")
        return {"text": f"Berhasil memperbarui isi {file_path}.", "type": "success"}

    def _intent_delete_file(self, text, entities, nlu):
        files = entities.get("filepath", [])
        if not files:
            return {"text": "File mana yang mau dihapus? Sebutkan nama file-nya.", "type": "ask"}
        return {"text": f"Yakin mau hapus {files[0]}? Ketik 'ya hapus {files[0]}' untuk konfirmasi.", "type": "confirm"}

    def _intent_explain(self, text, entities, nlu):
        thinking_result = self.thinking.process_with_mode(self, text, nlu)
        explanation = thinking_result.get("explanation", "")

        knowledge_results = self.knowledge.search_snippets(text)
        if knowledge_results:
            explanation += "\n\nContoh dari knowledge base:\n"
            for score, lang, snippet in knowledge_results[:2]:
                code = snippet["code"][:300]
                explanation += f"\n[{lang}]\n{code}\n"

        return {"text": explanation, "type": "explanation", "data": thinking_result}

    def _intent_debug(self, text, entities, nlu):
        thinking_result = self.thinking.process_with_mode(self, text, nlu)
        return {"text": thinking_result.get("explanation", "Kirimkan kode yang error untuk dianalisis."), "type": "debug", "data": thinking_result}

    def _intent_search(self, text, entities, nlu):
        query = text
        for word in ("cari", "carikan", "search", "find", "cari kode", "temukan"):
            query = query.replace(word, "").strip()

        try:
            from tool.internet_search import search_code
            results = search_code(query)

            if results and "error" not in results[0]:
                lines = [f"🔍 Hasil pencarian: {query}\n"]
                for i, r in enumerate(results, 1):
                    lines.append(f"  [{i}] {r.get('title', 'N/A')}")
                    lines.append(f"      {r.get('url', '')}")
                lines.append("\nKetik URL untuk mempelajari kode dari halaman tersebut.")
                return {"text": "\n".join(lines), "type": "search", "data": results}
            return {"text": "Tidak ada hasil ditemukan. Coba keyword lain.", "type": "search"}
        except Exception as e:
            return {"text": f"Gagal mencari: {e}", "type": "error"}

    def _intent_search_web(self, text, entities, nlu):
        query = text
        for word in ("carikan tentang", "berita tentang", "artikel", "cari", "carikan", "berita", "informasi", "info tentang", "search", "find"):
            query = query.replace(word, "").strip()

        try:
            import datetime
            now = datetime.datetime.now()
            month_year = now.strftime("%B %Y")
            
            # Auto-append current context if querying news or current info
            search_query = query
            if "berita" in query.lower() or "terkini" in query.lower() or "baru" in query.lower() or "informasi" in query.lower():
                search_query = f"{query} {month_year}"
                
            from tool.internet_search import search_web
            results = search_web(search_query)

            if results and "error" not in results[0]:
                lines = [f"[Hasil pencarian web: {query}]\n"]
                for i, r in enumerate(results, 1):
                    lines.append(f"  [{i}] {r.get('title', 'N/A')}")
                    lines.append(f"      {r.get('snippet', '')}")
                    lines.append(f"      {r.get('url', '')}")
                return {"text": "\n".join(lines), "type": "search", "data": results}
            return {"text": "Tidak ada hasil ditemukan. Coba keyword yang lebih spesifik.", "type": "search"}
        except Exception as e:
            return {"text": f"Gagal mencari: {e}", "type": "error"}

    def _intent_download_file(self, text, entities, nlu):
        urls = entities.get("url", [])
        if not urls:
            return {"text": "Tolong sertakan URL yang ingin didownload. Contoh: download https://example.com/file.zip", "type": "ask"}
        
        url = urls[0]
        try:
            import urllib.request
            import os
            from urllib.parse import urlparse
            
            # Extract filename or use default
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            if not filename:
                filename = "downloaded_file.bin"
            
            save_path = WORKSPACE_DIR / filename
            urllib.request.urlretrieve(url, save_path)
            return {"text": f"File berhasil didownload dan disimpan di: {save_path}", "type": "success"}
        except Exception as e:
            return {"text": f"Gagal mendownload file: {e}", "type": "error"}

    def _intent_read_news(self, text, entities, nlu):
        from tool.internet_search import search_news
        
        # Clean query
        query = text.lower()
        for word in ["baca berita", "cari berita", "berita", "news", "terbaru", "terkini"]:
            query = query.replace(word, "").strip()
        
        if not query:
            query = "teknologi programming" # Default topic
            
        try:
            results = search_news(query, max_results=5)
            if not results:
                return {"text": f"Belum ada berita terbaru untuk: '{query}'.", "type": "info"}
                
            lines = [f"📰 Berita Terkini: {query.title() if query != 'teknologi programming' else 'Teknologi & Programming'}\n"]
            for i, r in enumerate(results, 1):
                lines.append(f"  [{i}] {r.get('title', '')}")
                lines.append(f"      {r.get('snippet', '')}")
                lines.append(f"      {r.get('url', '')}")
            return {"text": "\n".join(lines), "type": "info"}
        except Exception as e:
            return {"text": f"Gagal mengambil berita: {e}", "type": "error"}

    def _intent_research_topic(self, text, entities, nlu):
        # AI Router + Google Search combo
        router = self._get_ai_router()
        if router and router.get_primary_provider() != "local":
            answer, provider = router.answer(f"Lakukan riset singkat dan detail tentang: {text}. Berikan penjelasan yang komprehensif.")
            if answer and len(answer) > 20:
                return {"text": f"[Riset AI via {provider}]\n{answer}", "type": "ai", "provider": provider}
        
        # Fallback to normal search
        return self._intent_search_web(text, entities, nlu)

    def _intent_learn(self, text, entities, nlu):
        urls = entities.get("url", [])
        if not urls:
            return {"text": "URL mana yang mau dipelajari? Tempel URL-nya.", "type": "ask"}

        url = urls[0]
        try:
            from tool.web_scraping import scrape_code_snippets, summarize_article
            
            summary_info = summarize_article(url)
            text_resp = ""
            if "error" not in summary_info:
                text_resp += f"[Ringkasan Artikel: {summary_info['title']}]\n"
                text_resp += f"{summary_info['summary']}\n\n"
                text_resp += f"Sumber Asli: {url}\n\n"

            snippets = scrape_code_snippets(url)
            if snippets:
                self.brain.train_from_web_data(snippets, source=url)
                self.save_all()
                text_resp += f"[OK] Berhasil mempelajari {len(snippets)} code snippets dari sumber ini."
            elif not text_resp:
                text_resp = "Tidak ditemukan artikel atau code di URL tersebut."
                
            return {"text": text_resp.strip(), "type": "success"}
        except Exception as e:
            return {"text": f"Gagal membaca dari URL: {e}", "type": "error"}

    def _intent_suggest(self, text, entities, nlu):
        suggestions = self.get_suggestions(text)
        line_suggestions = self.get_line_suggestions(text)

        if suggestions or line_suggestions:
            return {
                "text": "",
                "type": "suggestion",
                "suggestions": suggestions,
                "line_suggestions": line_suggestions,
            }
        return {"text": "Belum ada suggestion. Coba training dulu dari folder project kamu.", "type": "info"}

    def _intent_generate(self, text, entities, nlu):
        thinking_result = self.thinking.process_with_mode(self, text, nlu)
        suggestions = thinking_result.get("suggestions", [])

        response_text = ""
        if suggestions:
            response_text = "Berikut suggestion kode:\n\n"
            for item in suggestions[:5]:
                response_text += f"  {item.get('text', '')}\n"

        knowledge_results = self.knowledge.search_snippets(text)
        if knowledge_results:
            response_text += "\nContoh dari knowledge base:\n"
            for score, lang, snippet in knowledge_results[:2]:
                code = snippet["code"][:500]
                response_text += f"\n{code}\n"

        if not response_text:
            response_text = "Jelaskan lebih detail kode apa yang ingin dibuat."

        return {"text": response_text, "type": "generate", "data": thinking_result}

    def _intent_train(self, text, entities, nlu):
        path = str(WORKSPACE_DIR)

        files = entities.get("filepath", [])
        if files:
            path = files[0]

        if os.path.isdir(path):
            count = self.train_directory(path)
            self.save_all()
            return {"text": f"Training selesai! {count} file diproses, {self.brain.total_tokens_trained} tokens dipelajari.", "type": "success"}
        elif os.path.isfile(path):
            self.train_file(path)
            self.save_all()
            return {"text": f"File {path} berhasil di-train!", "type": "success"}
        return {"text": f"Path tidak ditemukan: {path}", "type": "error"}

    def _intent_stats(self, text, entities, nlu):
        stats = self.get_stats()
        model = stats.get("model", {})
        knowledge = stats.get("knowledge", {})
        scheduler = self.scheduler.get_stats()

        lines = [
            "📊 Statistik KokoAI",
            f"  🧠 Vocab: {model.get('vocab_size', 0)}",
            f"  📝 N-gram: {model.get('ngram_entries', 0)}",
            f"  🔗 Transitions: {model.get('transition_entries', 0)}",
            f"  📋 Line Patterns: {model.get('line_patterns', 0)}",
            f"  🔤 Total Tokens: {model.get('total_tokens_trained', 0)}",
            f"  📈 Training Sessions: {model.get('training_sessions', 0)}",
            f"  🎯 Akurasi: {model.get('accuracy', 0):.1f}%",
            f"  📚 Snippets: {knowledge.get('total_snippets', 0)}",
            f"  🧩 Patterns: {knowledge.get('total_patterns', 0)}",
            f"  🤖 Auto-training: {scheduler.get('total_sessions', 0)} sesi",
            f"  📖 Topic covered: {scheduler.get('topics_covered', 0)}",
        ]
        return {"text": "\n".join(lines), "type": "stats", "data": stats}

    def _intent_time(self, text, entities, nlu):
        from tool.time_date_today import get_now
        return {"text": f"🕐 {get_now()}", "type": "time"}

    def _intent_weather(self, text, entities, nlu):
        city = "Jakarta"
        cities = entities.get("city", [])
        if cities:
            city = cities[0]

        from tool.weather import get_weather
        weather = get_weather(city)
        if "error" in weather:
            return {"text": weather["error"], "type": "error"}
        return {
            "text": f"🌤️ Cuaca {city}: {weather['temp_c']}°C (Terasa {weather['feels_like_c']}°C), {weather['description']}, Kelembaban {weather['humidity']}%",
            "type": "weather",
        }

    def _intent_system(self, text, entities, nlu):
        from tool.cpu_usage import get_cpu_usage_bar
        from tool.ram_usage import get_ram_usage_bar
        return {"text": f"💻 System Monitor:\n  {get_cpu_usage_bar()}\n  {get_ram_usage_bar()}", "type": "system"}

    def _intent_save(self, text, entities, nlu):
        self.save_all()
        return {"text": "Model dan knowledge base berhasil disimpan!", "type": "success"}

    def _intent_list_files(self, text, entities, nlu):
        from tool.filesystem import get_directory_tree
        path = str(WORKSPACE_DIR)
        files = entities.get("filepath", [])
        if files:
            path = files[0]
        tree = get_directory_tree(path)
        return {"text": f"[DIR] {path}:\n{tree}" if tree else f"[Kosong] Folder: {path}", "type": "tree"}

    def _intent_run_command(self, text, entities, nlu):
        cmd = text
        for word in ("jalankan terminal", "eksekusi perintah", "buka cmd", "jalankan cmd", "jalankan", "eksekusi", "run command", "execute", "run", "cmd", "terminal", "start"):
            cmd = cmd.lower().replace(word, "")
        cmd = cmd.strip()

        if not cmd:
            return {"text": "Perintah apa yang ingin dijalankan? (contoh: 'jalankan npm install' atau 'jalankan python script.py')", "type": "ask"}
        return {"text": f"Anda akan menjalankan perintah: `{cmd}`", "type": "confirm_run", "data": cmd}

    def _intent_unknown(self, text, entities, nlu):
        suggestions = self.get_suggestions(text)
        if suggestions:
            return {
                "text": "",
                "type": "suggestion",
                "suggestions": suggestions,
                "line_suggestions": self.get_line_suggestions(text),
            }

        context = self.memory.get_context_summary()
        return {
            "text": "Maaf, saya belum mengerti maksudmu. Coba jelaskan lebih detail, atau ketik:\n"
                    "  - Nama file untuk dibuat/dibaca\n"
                    "  - Kode untuk mendapat suggestion\n"
                    "  - Pertanyaan tentang programming\n"
                    "  - 'bantuan' untuk melihat fitur yang tersedia",
            "type": "unknown",
        }

    def _generate_text_content(self, request_text, filename):
        import re
        num_match = re.search(r'(\d+)\s*(?:buah|item|baris|data|list|daftar)?', request_text)
        count = int(num_match.group(1)) if num_match else 5

        if "lagu" in request_text or "musik" in request_text or "song" in request_text:
            songs = [
                "1. Bohemian Rhapsody - Queen",
                "2. Hotel California - Eagles",
                "3. Imagine - John Lennon",
                "4. Smells Like Teen Spirit - Nirvana",
                "5. Billie Jean - Michael Jackson",
                "6. Stairway to Heaven - Led Zeppelin",
                "7. Shape of You - Ed Sheeran",
                "8. Blinding Lights - The Weeknd",
                "9. Somebody That I Used to Know - Gotye",
                "10. Rolling in the Deep - Adele",
            ]
            return "\n".join(songs[:count])

        if "todo" in request_text or "tugas" in request_text or "task" in request_text:
            tasks = [f"{i}. [ ] Tugas {i}" for i in range(1, count + 1)]
            return "\n".join(tasks)

        if "nama" in request_text or "name" in request_text:
            names = ["1. Ahmad", "2. Budi", "3. Citra", "4. Dewi", "5. Eka",
                     "6. Fajar", "7. Gita", "8. Hana", "9. Indra", "10. Joko"]
            return "\n".join(names[:count])

        try:
            from tool.internet_search import search_web
            topic = request_text
            for w in ("isi", "tulis", "isikan", "masukkan", "tambah", "berikan", "kasih",
                      "file", "buah", "yang", "anda", "suka", "di", "pada", "ke", "dalam"):
                topic = topic.replace(w, "")
            topic = " ".join(topic.split()).strip()
            if topic and len(topic) > 2:
                results = search_web(topic, 3)
                if results and "error" not in results[0]:
                    lines = []
                    for i, r in enumerate(results, 1):
                        lines.append(f"{i}. {r.get('title', '')}")
                        lines.append(f"   {r.get('snippet', '')}")
                    return "\n".join(lines)
        except Exception:
            pass

        lines = [f"{i}. Item {i}" for i in range(1, count + 1)]
        return "\n".join(lines)

    def _detect_html_section(self, text):
        sections = {
            "footer": ["footer", "kaki", "kaki halaman"],
            "header": ["header", "kepala", "navbar", "navigasi", "nav"],
            "hero": ["hero", "banner", "jumbotron", "splash"],
        }
        for section, keywords in sections.items():
            for kw in keywords:
                if kw in text:
                    return section
        return None

    def _inject_html_section(self, content, section, description):
        import re
        if section == "footer":
            footer_html = '''
    <footer style="background:#1f2937;color:#d1d5db;padding:40px 20px;margin-top:40px;">
        <div style="max-width:1000px;margin:auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:30px;">
            <div>
                <h4 style="color:white;margin-bottom:10px;">Tentang Kami</h4>
                <p style="font-size:0.9em;">Kami menyediakan produk berkualitas tinggi dengan pelayanan terbaik.</p>
            </div>
            <div>
                <h4 style="color:white;margin-bottom:10px;">Link Cepat</h4>
                <p style="font-size:0.9em;">Beranda | Produk | Kontak | FAQ</p>
            </div>
            <div>
                <h4 style="color:white;margin-bottom:10px;">Kontak</h4>
                <p style="font-size:0.9em;">Email: info@example.com<br>Telp: +62 812-3456-7890</p>
            </div>
        </div>
        <div style="text-align:center;margin-top:20px;padding-top:20px;border-top:1px solid #374151;">
            <p style="font-size:0.85em;">&copy; 2026 All Rights Reserved.</p>
        </div>
    </footer>'''
            content = re.sub(r'<footer[\s\S]*?</footer>', '', content, flags=re.IGNORECASE)
            content = content.replace("</body>", f"{footer_html}\n</body>")
            return content

        if section == "hero":
            hero_html = '''
    <section style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:100px 20px;text-align:center;">
        <h1 style="font-size:3em;margin-bottom:15px;">Produk Terbaik Untuk Anda</h1>
        <p style="font-size:1.3em;opacity:0.9;max-width:600px;margin:auto;">Temukan koleksi eksklusif dengan kualitas premium dan harga terjangkau.</p>
        <button style="margin-top:25px;padding:15px 40px;background:white;color:#764ba2;border:none;border-radius:50px;font-size:1.1em;cursor:pointer;">Lihat Koleksi</button>
    </section>'''
            content = re.sub(r'<header[\s\S]*?</header>', hero_html, content, count=1, flags=re.IGNORECASE)
            if hero_html not in content:
                content = content.replace("<body>", f"<body>\n{hero_html}", 1)
            return content

        if section == "header":
            nav_html = '''
    <nav style="background:#111827;color:white;padding:15px 30px;display:flex;justify-content:space-between;align-items:center;">
        <div style="font-weight:bold;font-size:1.2em;">Brand</div>
        <div>
            <a href="#" style="color:#d1d5db;text-decoration:none;margin-left:20px;">Beranda</a>
            <a href="#" style="color:#d1d5db;text-decoration:none;margin-left:20px;">Produk</a>
            <a href="#" style="color:#d1d5db;text-decoration:none;margin-left:20px;">Tentang</a>
            <a href="#" style="color:#d1d5db;text-decoration:none;margin-left:20px;">Kontak</a>
        </div>
    </nav>'''
            existing_nav = re.search(r'<nav[\s\S]*?</nav>', content, flags=re.IGNORECASE)
            if existing_nav:
                content = content[:existing_nav.start()] + nav_html + content[existing_nav.end():]
            else:
                content = content.replace("<body>", f"<body>\n{nav_html}", 1)
            return content

        return content

    def _generate_file_content(self, filename, description, language):
        ext = Path(filename).suffix.lower()

        if ext == ".py":
            return f'def main():\n    pass\n\n\nif __name__ == "__main__":\n    main()\n'
        elif ext in (".js", ".ts"):
            return f'console.log("Hello from {filename}");\n'
        elif ext == ".html":
            name = Path(filename).stem
            is_landing = "landing" in description.lower() or "landing" in name.lower() or "index" in name.lower()
            
            if is_landing:
                title = name.title()
                subtitle = "Solusi terbaik untuk kebutuhan Anda. Cepat, modern, dan handal."
                
                import re
                m = re.search(r'(?:jualan|berisi|tentang|untuk) ([\w\s]+)', description.lower())
                if m:
                    extracted = m.group(1).replace('.html', '').replace('index', '').replace('landing page', '').strip().title()
                    if extracted:
                        title = extracted.title()
                        subtitle = f"Temukan penawaran terbaik untuk {title}. Kualitas juara, harga bersahabat!"

                if "tailwind" in description.lower():
                    return f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Landing Page</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 text-gray-800 font-sans">
    <header class="bg-gradient-to-r from-blue-500 to-indigo-600 text-white py-20 px-4 text-center">
        <h1 class="text-5xl font-bold mb-4 drop-shadow-md">{title}</h1>
        <p class="text-xl max-w-2xl mx-auto opacity-90">{subtitle}</p>
        <button class="mt-8 bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-8 rounded-full shadow-lg transition transform hover:scale-105">
            Pesan Sekarang
        </button>
    </header>
    <main class="max-w-5xl mx-auto px-4 -mt-10 mb-16 relative z-10">
        <div class="bg-white rounded-xl shadow-xl p-8">
            <h2 class="text-3xl font-bold text-center mb-10 text-gray-800">Kenapa Memilih Kami?</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="text-center p-6 bg-gray-50 border border-gray-100 rounded-lg hover:shadow-lg transition">
                    <h3 class="text-xl font-bold text-indigo-600 mb-3">Kualitas Tinggi</h3>
                    <p class="text-gray-600">Material premium yang dirancang agar awet dan nyaman dipakai.</p>
                </div>
                <div class="text-center p-6 bg-gray-50 border border-gray-100 rounded-lg hover:shadow-lg transition">
                    <h3 class="text-xl font-bold text-indigo-600 mb-3">Desain Mewah</h3>
                    <p class="text-gray-600">Gaya elegan dan eksklusif yang menyesuaikan tren modern.</p>
                </div>
                <div class="text-center p-6 bg-gray-50 border border-gray-100 rounded-lg hover:shadow-lg transition">
                    <h3 class="text-xl font-bold text-indigo-600 mb-3">Harga Terbaik</h3>
                    <p class="text-gray-600">Kualitas kelas atas dengan penawaran harga yang bersahabat.</p>
                </div>
            </div>
        </div>
    </main>
    <footer class="text-center py-6 text-gray-500 border-t border-gray-200 mt-auto">
        &copy; 2026 {title}. Dibuat dengan semangat oleh KokoAI.
    </footer>
</body>
</html>'''

                return f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Landing Page</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; padding: 0; background-color: #f8f9fa; color: #333;
        }}
        header {{
            background: linear-gradient(135deg, #FF6B6B, #C0392B);
            color: white; padding: 80px 20px; text-align: center;
        }}
        h1 {{ margin: 0; font-size: 3.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        p.lead {{ font-size: 1.3em; margin-top: 15px; opacity: 0.95; }}
        .container {{
            max-width: 1000px; margin: -30px auto 40px; padding: 30px;
            background: white; border-radius: 12px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }}
        .features {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; margin-top: 30px;
        }}
        .feature-card {{
            padding: 25px; background: #fff; border: 1px solid #eee; border-radius: 8px; text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .feature-card:hover {{
            transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        button {{
            background: #27ae60; color: white; border: none; padding: 15px 35px;
            font-size: 1.2em; border-radius: 50px; cursor: pointer; margin-top: 25px; 
            transition: all 0.3s; box-shadow: 0 4px 15px rgba(39, 174, 96, 0.4);
        }}
        button:hover {{ background: #219653; transform: scale(1.05); }}
        footer {{ text-align: center; padding: 20px; margin-top: 40px; color: #6c757d; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <header>
        <h1>Selamat Datang di {title}</h1>
        <p class="lead">{subtitle}</p>
        <button>Pesan Sekarang</button>
    </header>
    <div class="container">
        <h2 style="text-align: center;">Kenapa Memilih Kami?</h2>
        <div class="features">
            <div class="feature-card">
                <h3>Kualitas Tinggi</h3>
                <p>Website yang cepat dan dioptimalkan dengan baik.</p>
            </div>
            <div class="feature-card">
                <h3>Desain Mewah</h3>
                <p>Tampilan yang responsif dan memukau di semua perangkat.</p>
            </div>
            <div class="feature-card">
                <h3>Keamanan Terbaik</h3>
                <p>Berkomitmen menjaga privasi dan data Anda tetap aman.</p>
            </div>
        </div>
    </div>
    <footer>
        <p>&copy; 2026 {name.title()}. Hak cipta dilindungi.</p>
    </footer>
</body>
</html>
'''
            else:
                return f'<!DOCTYPE html>\n<html lang="id">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{name}</title>\n</head>\n<body>\n    <h1>{name}</h1>\n</body>\n</html>\n'
        elif ext == ".css":
            return "* {\n    margin: 0;\n    padding: 0;\n    box-sizing: border-box;\n}\n"
        return ""

    def get_suggestions(self, code_context, language=None, max_suggestions=None):
        if not code_context:
            return []
        if language is None:
            language = self.tokenizer.detect_language(code_context)
        self.current_language = language
        max_sugg = max_suggestions or MAX_SUGGESTIONS
        return self.brain.predict(code_context, max_sugg, language)

    def get_line_suggestions(self, code_context, language=None):
        if language is None:
            language = self.tokenizer.detect_language(code_context)
        return self.brain.predict_line(code_context, language)

    def accept_suggestion(self, context, accepted_text):
        self.brain.self_learn(context, accepted_text)

    def train_file(self, filepath):
        return self.brain.train_from_file(filepath)

    def train_directory(self, directory):
        return self.brain.train_from_directory(directory)

    def train_from_internet(self, query, language="python"):
        from tool.internet_search import search_code
        from tool.web_scraping import scrape_code_snippets

        try:
            search_results = search_code(query, language)
            total = 0
            for result in search_results[:5]:
                url = result.get("url", "")
                if url:
                    snippets = scrape_code_snippets(url, language)
                    if snippets:
                        self.brain.train_from_web_data(snippets, language, source=url)
                        total += len(snippets)
            self.brain.save_model()
            self.knowledge.save()
            return total
        except Exception:
            return 0

    def search_knowledge(self, query, language=None):
        return self.knowledge.search_snippets(query, language)

    def get_stats(self):
        return {
            "app": APP_NAME,
            "version": VERSION,
            "model": self.brain.get_model_stats(),
            "knowledge": self.knowledge.get_stats(),
            "scheduler": self.scheduler.get_stats(),
            "is_running": self.is_running,
            "current_language": self.current_language,
            "watched_files": len(self.watched_files),
            "conversation_turns": len(self.memory.turns),
        }

    def _initial_training(self):
        if WORKSPACE_DIR.exists():
            count = self.brain.train_from_directory(WORKSPACE_DIR)
            if count > 0:
                self.brain.save_model()
                self.knowledge.save()
            return count
        return 0

    def _start_file_watcher(self):
        if not WORKSPACE_DIR.exists():
            WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

        handler = FileChangeHandler(self)
        self.observer = Observer()
        self.observer.schedule(handler, str(WORKSPACE_DIR), recursive=True)
        self.observer.daemon = True
        self.observer.start()

    def _on_file_changed(self, filepath):
        try:
            self.brain.train_from_file(filepath)
            self.current_file = filepath
            ext = filepath.suffix.lower()
            self.current_language = SUPPORTED_EXTENSIONS.get(ext, "python")
        except Exception:
            pass

    def _start_auto_training(self):
        def auto_train_loop():
            while self.is_running:
                time.sleep(TRAINING_INTERVAL * 60)
                if not self.is_running:
                    break
                try:
                    count = self.brain.train_from_directory(WORKSPACE_DIR)
                    if count > 0:
                        self.brain.save_model()
                        self.knowledge.save()
                except Exception:
                    pass

        self.training_thread = threading.Thread(target=auto_train_loop, daemon=True)
        self.training_thread.start()

    def save_all(self):
        self.brain.save_model()
        self.knowledge.save()
        self.memory.save()
