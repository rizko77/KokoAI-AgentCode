import os
import sys
import time
import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import (
    APP_NAME, VERSION, BUILD, AUTHOR,
    WORKSPACE_DIR, DATA_DIR,
)
from core.engine import CoreEngine
from prompt.template import get_initial_training_data

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown
    from rich import print as rprint
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


class KokoAIApp:

    def __init__(self):
        self.engine = CoreEngine()
        self.start_time = time.time()
        self.running = True

    def start(self):
        signal.signal(signal.SIGINT, self._handle_exit)
        self._show_welcome()
        self._initial_template_training()
        self.engine.start()
        self._main_loop()

    def _show_welcome(self):
        print(f"\n{APP_NAME} | Build {BUILD}")
        print("-" * 50)
        
        stats = self.engine.get_stats()
        model = stats.get("model", {})
        knowledge = stats.get("knowledge", {})
        
        print(f"Workspace: {WORKSPACE_DIR}")
        print(f"Data Dir : {DATA_DIR}")
        print(f"Vocab    : {model.get('vocab_size', 0)}")
        print(f"Rules    : {knowledge.get('total_snippets', 0)} snippets")
        print("-" * 50)
        print("Mulai ketikkan perintah Anda.\n")

    def _initial_template_training(self):
        templates = get_initial_training_data()
        for language, codes in templates.items():
            for code in codes:
                self.engine.brain.train(code, language)

    def _main_loop(self):
        while self.running:
            try:
                user_input = input("KokoAI> ")
                if not user_input.strip():
                    continue

                self._process_input(user_input.strip())

            except EOFError:
                self._handle_exit()
            except KeyboardInterrupt:
                print("\nKeyboard Interrupt")
                self._handle_exit()

    def _process_input(self, user_input):
        if user_input.startswith("/"):
            self._handle_slash_command(user_input)
            return

        response = self.engine.process_input(user_input)
        self._display_response(response)

        if response.get("exit"):
            self._handle_exit()

    def _handle_slash_command(self, command):
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        commands = {
            "/help": self._cmd_help,
            "/suggest": self._cmd_suggest,
            "/complete": self._cmd_complete,
            "/train": self._cmd_train,
            "/trainfile": self._cmd_trainfile,
            "/search": self._cmd_search,
            "/learn": self._cmd_learn,
            "/docs": self._cmd_docs,
            "/stats": self._cmd_stats,
            "/system": self._cmd_system,
            "/time": self._cmd_time,
            "/weather": self._cmd_weather,
            "/tree": self._cmd_tree,
            "/save": self._cmd_save,
            "/watch": self._cmd_watch,
            "/mode": self._cmd_mode,
            "/reset": self._cmd_reset,
            "/clear": self._cmd_clear,
            "/autotrain": self._cmd_autotrain,
            "/exit": self._handle_exit,
            "/quit": self._handle_exit,
        }

        handler = commands.get(cmd)
        if handler:
            handler(args)
        else:
            self._print_error(f"Command tidak dkenal: {cmd}")

    def _display_response(self, response):
        resp_type = response.get("type", "text")
        text = response.get("text", "")
        provider = response.get("provider", "")

        if resp_type == "suggestion":
            suggestions = response.get("suggestions", [])
            line_suggestions = response.get("line_suggestions", [])
            if suggestions:
                self._print_suggestions(suggestions)
            if line_suggestions:
                print()
                self._print_line_suggestions(line_suggestions)
            if not suggestions and not line_suggestions:
                self._print_info("Belum ada suggestion.")

        elif resp_type == "error":
            self._print_error(text)

        elif resp_type in ("success", "ok"):
            self._print_success(text)

        elif resp_type == "confirm_run":
            cmd = response.get("data", "")
            print(f"\n[KONFIRMASI] Akan menjalankan perintah terminal: {cmd}")
            ans = input("Lanjutkan eksekusi? (y/n) > ")
            if ans.lower() == 'y':
                import os
                print(f"Menjalankan: {cmd}")
                os.system(cmd)
                print("Eksekusi selesai.")
            else:
                self._print_info("Eksekusi dibatalkan.")

        elif resp_type == "ai":
            # Response dari Gemini/Claude/OpenAI
            tag = f" [via {provider}]" if provider and provider != "local" else ""
            print(f"\n[KokoAI{tag}]")
            print(text)

        elif resp_type in ("info", "search"):
            print()
            print(text)

        elif resp_type == "ask":
            # AI meminta klarifikasi
            print(f"\n[?] {text}")

        elif resp_type in ("file_content", "stats", "greeting", "help"):
            print(text)

        else:
            if text:
                print(text)

    def _cmd_help(self, args=""):
        from prompt.static import HELP_MESSAGE
        print(HELP_MESSAGE)

    def _cmd_suggest(self, args=""):
        if not args:
            self._print_error("Usage: /suggest <kode>")
            return
        suggestions = self.engine.get_suggestions(args)
        self._print_suggestions(suggestions)

    def _cmd_complete(self, args=""):
        if not args:
            self._print_error("Usage: /complete <kode>")
            return
        line_suggestions = self.engine.get_line_suggestions(args)
        self._print_line_suggestions(line_suggestions)

    def _cmd_train(self, args=""):
        path = args or str(WORKSPACE_DIR)

        if not os.path.isdir(path):
            self._print_error(f"Direktori tidak ditemukan: {path}")
            return

        self._print_status(f"Sedang training dari {path}...")

        if HAS_RICH:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Training dari {path}...", total=None)
                count = self.engine.train_directory(path)
                progress.update(task, description=f"Selesai! {count} file diproses.")
        else:
            count = self.engine.train_directory(path)

        tokens = self.engine.brain.total_tokens_trained
        self._print_success(f"Training selesai! {count} file diproses, {tokens} tokens dipelajari.")
        self.engine.save_all()

    def _cmd_trainfile(self, args=""):
        if not args:
            self._print_error("Usage: /trainfile <filepath>")
            return
        if not os.path.isfile(args):
            self._print_error(f"File tidak ditemukan: {args}")
            return
        success = self.engine.train_file(args)
        if success:
            self._print_success(f"File {args} berhasil di-train!")
            self.engine.save_all()
        else:
            self._print_error(f"Gagal training dari {args}")

    def _cmd_search(self, args=""):
        if not args:
            self._print_error("Usage: /search <query>")
            return
        self._print_status(f"Mencari: {args}...")
        try:
            from tool.internet_search import search_code
            results = search_code(args)
            if not results or (results and "error" in results[0]):
                self._print_error("Gagal terhubung ke internet.")
                return

            if HAS_RICH:
                table = Table(title=f"🔍 Hasil: {args}", border_style="cyan")
                table.add_column("#", style="dim", width=3)
                table.add_column("Title", style="cyan", max_width=50)
                table.add_column("URL", style="dim", max_width=40)
                for i, result in enumerate(results, 1):
                    table.add_row(str(i), result.get("title", "N/A")[:50], result.get("url", "N/A")[:40])
                console.print(table)
            else:
                print(f"\n🔍 Hasil: {args}")
                for i, result in enumerate(results, 1):
                    print(f"  [{i}] {result.get('title', 'N/A')}")
                    print(f"      {result.get('url', 'N/A')}")
        except Exception as e:
            self._print_error(f"Error: {e}")

    def _cmd_learn(self, args=""):
        if not args:
            self._print_error("Usage: /learn <url>")
            return
        self._print_status(f"Mengambil kode dari {args}...")
        try:
            from tool.web_scraping import scrape_code_snippets
            snippets = scrape_code_snippets(args)
            if snippets:
                self.engine.brain.train_from_web_data(snippets, source=args)
                self.engine.save_all()
                self._print_success(f"Berhasil mempelajari {len(snippets)} snippets dari {args}!")
            else:
                self._print_error("Tidak ditemukan code snippets di URL tersebut.")
        except Exception as e:
            self._print_error(f"Error: {e}")

    def _cmd_docs(self, args=""):
        if not args:
            self._print_error("Usage: /docs <topic>")
            return
        self._print_status(f"Mencari dokumentasi: {args}...")
        try:
            from tool.internet_search import search_documentation
            results = search_documentation(args)
            if results:
                for i, r in enumerate(results, 1):
                    if HAS_RICH:
                        console.print(f"  [cyan][{i}][/cyan] {r.get('title', 'N/A')}")
                        console.print(f"      [dim]{r.get('url', 'N/A')}[/dim]")
                    else:
                        print(f"  [{i}] {r.get('title', 'N/A')}")
                        print(f"      {r.get('url', 'N/A')}")
            else:
                self._print_error("Tidak ada hasil.")
        except Exception as e:
            self._print_error(f"Error: {e}")

    def _cmd_stats(self, args=""):
        stats = self.engine.get_stats()
        model = stats.get("model", {})
        knowledge = stats.get("knowledge", {})
        scheduler = stats.get("scheduler", {})

        if HAS_RICH:
            table = Table(title="📊 Statistik KokoAI", border_style="cyan")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white", justify="right")

            table.add_row("🧠 Vocab Size", str(model.get("vocab_size", 0)))
            table.add_row("📝 N-gram Entries", str(model.get("ngram_entries", 0)))
            table.add_row("🔗 Transitions", str(model.get("transition_entries", 0)))
            table.add_row("📋 Line Patterns", str(model.get("line_patterns", 0)))
            table.add_row("📦 Block Patterns", str(model.get("block_patterns", 0)))
            table.add_row("🔤 Total Tokens", str(model.get("total_tokens_trained", 0)))
            table.add_row("📈 Training Sessions", str(model.get("training_sessions", 0)))
            table.add_row("🎯 Accuracy", f"{model.get('accuracy', 0):.1f}%")
            table.add_row("", "")
            table.add_row("📚 Code Snippets", str(knowledge.get("total_snippets", 0)))
            table.add_row("🧩 Patterns", str(knowledge.get("total_patterns", 0)))
            table.add_row("📖 Documents", str(knowledge.get("total_docs", 0)))
            table.add_row("📝 Training Data", str(knowledge.get("total_training", 0)))
            table.add_row("🌐 Languages", ", ".join(knowledge.get("languages", [])))
            table.add_row("", "")
            table.add_row("🤖 Auto Sessions", str(scheduler.get("total_sessions", 0)))
            table.add_row("📖 Topics Covered", str(scheduler.get("topics_covered", 0)))
            table.add_row("🔄 Scheduler", "Active" if scheduler.get("is_running") else "Inactive")

            from tool.time_date_today import get_uptime_str
            table.add_row("⏱️ Uptime", get_uptime_str(self.start_time))
            table.add_row("💬 Conversations", str(stats.get("conversation_turns", 0)))

            console.print(table)
        else:
            print("\n📊 STATISTIK KOKOAI")
            print(f"  Vocab Size: {model.get('vocab_size', 0)}")
            print(f"  N-gram Entries: {model.get('ngram_entries', 0)}")
            print(f"  Total Tokens: {model.get('total_tokens_trained', 0)}")
            print(f"  Snippets: {knowledge.get('total_snippets', 0)}")

    def _cmd_system(self, args=""):
        from tool.cpu_usage import get_cpu_usage_bar
        from tool.ram_usage import get_ram_usage_bar
        if HAS_RICH:
            console.print(Panel(
                f"{get_cpu_usage_bar()}\n{get_ram_usage_bar()}",
                title="💻 System Monitor",
                border_style="green",
            ))
        else:
            print(f"\n💻 System Monitor")
            print(f"  {get_cpu_usage_bar()}")
            print(f"  {get_ram_usage_bar()}")

    def _cmd_time(self, args=""):
        from tool.time_date_today import get_now
        print(f"🕐 {get_now()}")

    def _cmd_weather(self, args=""):
        from tool.weather import get_weather
        city = args or "Jakarta"
        self._print_status(f"Mengambil cuaca {city}...")
        weather = get_weather(city)
        if "error" in weather:
            self._print_error(weather["error"])
        else:
            if HAS_RICH:
                console.print(Panel(
                    f"🌡️ Suhu: {weather['temp_c']}°C (Terasa: {weather['feels_like_c']}°C)\n"
                    f"☁️ Kondisi: {weather['description']}\n"
                    f"💧 Kelembaban: {weather['humidity']}%\n"
                    f"💨 Angin: {weather['wind_speed']} km/h {weather['wind_dir']}",
                    title=f"🌤️ Cuaca {city}",
                    border_style="yellow",
                ))
            else:
                print(f"\n🌤️ Cuaca {city}")
                print(f"  Suhu: {weather['temp_c']}°C")
                print(f"  Kondisi: {weather['description']}")

    def _cmd_tree(self, args=""):
        from tool.filesystem import get_directory_tree
        path = args or str(WORKSPACE_DIR)
        tree = get_directory_tree(path)
        if tree:
            if HAS_RICH:
                console.print(Panel(tree, title=f"📁 {path}", border_style="blue"))
            else:
                print(f"\n📁 {path}")
                print(tree)
        else:
            self._print_error(f"Directory kosong atau tidak ditemukan: {path}")

    def _cmd_save(self, args=""):
        self.engine.save_all()
        self._print_success("Model dan knowledge base berhasil disimpan!")

    def _cmd_watch(self, args=""):
        if self.engine.observer and self.engine.observer.is_alive():
            self._print_success(f"File watcher AKTIF untuk {WORKSPACE_DIR}")
        else:
            self._print_error("File watcher TIDAK AKTIF")

    def _cmd_mode(self, args=""):
        if args:
            result = self.engine.thinking.set_mode(args.strip())
            if result:
                self._print_success(f"Mode diubah ke: {result['name']}")
            else:
                self._print_error(f"Mode tidak valid. Pilih: thinking, reasoning, medium, fast")
        else:
            modes = self.engine.thinking.get_all_modes()
            if HAS_RICH:
                for mode in modes:
                    current = " [green]← ACTIVE[/green]" if mode["is_current"] else ""
                    console.print(f"  {mode['display_name']}: {mode['description']}{current}")
            else:
                for mode in modes:
                    current = " ← ACTIVE" if mode["is_current"] else ""
                    print(f"  {mode['display_name']}: {mode['description']}{current}")

    def _cmd_autotrain(self, args=""):
        if args.lower() == "now":
            self._print_status("Menjalankan auto-training...")
            if HAS_RICH:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Auto-training dari internet...", total=None)
                    session = self.engine.scheduler.force_training()
                    progress.update(task, description="Selesai!")
            else:
                session = self.engine.scheduler.force_training()
            self._print_success(
                f"Auto-training selesai! Files: {session.get('files_trained', 0)}, "
                f"Snippets: {session.get('snippets_learned', 0)}"
            )
        else:
            stats = self.engine.scheduler.get_stats()
            if HAS_RICH:
                console.print(Panel(
                    f"Status: {'Active' if stats['is_running'] else 'Inactive'}\n"
                    f"Interval: {stats['interval_minutes']} menit\n"
                    f"Total Sessions: {stats['total_sessions']}\n"
                    f"Snippets Learned: {stats['total_snippets_learned']}\n"
                    f"Topics Covered: {stats['topics_covered']}",
                    title="🤖 Auto Training",
                    border_style="magenta",
                ))
                console.print("[dim]Ketik /autotrain now untuk training sekarang[/dim]")
            else:
                print(f"\nAuto Training: {'Active' if stats['is_running'] else 'Inactive'}")
                print(f"Sessions: {stats['total_sessions']}")

    def _cmd_reset(self, args=""):
        confirm = input("Yakin reset model? Semua training akan hilang! (y/n): ")
        if confirm.lower() == "y":
            self.engine.brain.reset_model()
            self._print_success("Model berhasil di-reset!")
        else:
            print("Batal.")

    def _cmd_clear(self, args=""):
        os.system("cls" if os.name == "nt" else "clear")

    def _print_suggestions(self, suggestions):
        if not suggestions:
            self._print_info("Tidak ada suggestion")
            return

        print(f"\n[Suggestions ({len(suggestions)}):]")
        for i, (text, score) in enumerate(suggestions, 1):
            print(f"  [{i}] {text}  ({score:.1%})")

    def _print_line_suggestions(self, suggestions):
        if not suggestions:
            return

        print(f"\n[Line Completions ({len(suggestions)}):]")
        for i, (text, score) in enumerate(suggestions, 1):
            print(f"  [{i}] {text}")

    def _print_success(self, message):
        print(f"[OK] {message}")

    def _print_error(self, message):
        print(f"[ERROR] {message}")

    def _print_status(self, message):
        print(f"[STATUS] {message}")

    def _print_info(self, message):
        print(f"[INFO] {message}")

    def _handle_exit(self, *args):
        self.running = False
        print("\n[INFO] Menyimpan model dan knowledge...")
        self.engine.stop()
        print("[INFO] Sampai jumpa!")
        sys.exit(0)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - AI Coding Assistant Lokal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python main.py                        Mode interaktif
  python main.py --train ./myproject    Training dari folder
  python main.py --stats                Lihat statistik model
  python main.py --search "python sort" Cari code di internet
  python main.py --autotrain            Jalankan auto-training
        """
    )
    parser.add_argument("--train", type=str, help="Training dari folder")
    parser.add_argument("--trainfile", type=str, help="Training dari file")
    parser.add_argument("--stats", action="store_true", help="Tampilkan statistik")
    parser.add_argument("--search", type=str, help="Cari code di internet")
    parser.add_argument("--suggest", type=str, help="Dapatkan suggestion untuk kode")
    parser.add_argument("--autotrain", action="store_true", help="Jalankan auto-training")

    args = parser.parse_args()

    app = KokoAIApp()

    if args.train:
        app._show_welcome()
        app._cmd_train(args.train)
        app._cmd_save()
    elif args.trainfile:
        app._show_welcome()
        app._cmd_trainfile(args.trainfile)
        app._cmd_save()
    elif args.stats:
        app._show_welcome()
        app._cmd_stats()
    elif args.search:
        app._show_welcome()
        app._cmd_search(args.search)
    elif args.suggest:
        app._show_welcome()
        app._initial_template_training()
        app._cmd_suggest(args.suggest)
    elif args.autotrain:
        app._show_welcome()
        app._cmd_autotrain("now")
    else:
        app.start()


if __name__ == "__main__":
    main()
