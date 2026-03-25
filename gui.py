"""
KokoAI 2.1 - GUI Tkinter
Antarmuka grafis modern untuk KokoAI AgentCode
Jalankan: python gui.py
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
import os
import sys
import datetime
from pathlib import Path

# Pastikan root project ada di sys.path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Warna & Font (Dark Theme) ─────────────────────────────────────
COLORS = {
    "bg":          "#0d1117",   # GitHub dark background
    "bg_panel":    "#161b22",   # Panel/sidebar
    "bg_input":    "#21262d",   # Input fields
    "bg_msg_ai":   "#1c2128",   # AI message bubble
    "bg_msg_user": "#0d2137",   # User message bubble
    "accent":      "#58a6ff",   # Primary blue
    "accent2":     "#3fb950",   # Green (success)
    "accent3":     "#f85149",   # Red (error)
    "accent4":     "#d29922",   # Yellow (warning)
    "text":        "#e6edf3",   # Primary text
    "text_dim":    "#8b949e",   # Dimmed text
    "border":      "#30363d",   # Border color
    "hover":       "#1f6feb",   # Hover state
}

FONTS = {
    "title":  ("Segoe UI", 14, "bold"),
    "header": ("Segoe UI", 11, "bold"),
    "body":   ("Segoe UI", 10),
    "code":   ("Consolas", 10),
    "small":  ("Segoe UI", 9),
    "tiny":   ("Segoe UI", 8),
}


class KokoAIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("KokoAI 2.1 — AgentCode")
        self.root.geometry("1100x720")
        self.root.minsize(800, 500)
        self.root.configure(bg=COLORS["bg"])

        # Set icon jika ada
        icon_path = ROOT / "assets" / "icon.ico"
        try:
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass

        self._engine = None
        self._response_queue = queue.Queue()
        self._history = []
        self._thinking = False

        self._build_ui()
        self._load_engine_async()
        self._poll_queue()

    # ── Engine Loading ────────────────────────────────────────────

    def _load_engine_async(self):
        self._set_status("Memuat KokoAI Engine...", color=COLORS["accent4"])
        t = threading.Thread(target=self._load_engine_thread, daemon=True)
        t.start()

    def _load_engine_thread(self):
        try:
            from core.engine import CoreEngine
            self._engine = CoreEngine()
            self._engine.start()
            self._response_queue.put(("status", "KokoAI siap! Ketikkan perintah Anda.", COLORS["accent2"]))
        except Exception as e:
            self._response_queue.put(("status", f"Error loading engine: {e}", COLORS["accent3"]))

    # ── UI Builder ────────────────────────────────────────────────

    def _build_ui(self):
        # ─ Top bar
        self._build_topbar()
        # ─ Main area (sidebar + chat)
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self._build_sidebar(main)
        self._build_chat_area(main)

        # ─ Bottom input bar
        self._build_input_bar()

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=COLORS["bg_panel"], height=42, relief="flat")
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False)

        # Logo
        tk.Label(
            bar, text="🤖 KokoAI", font=FONTS["title"],
            bg=COLORS["bg_panel"], fg=COLORS["accent"]
        ).pack(side=tk.LEFT, padx=16, pady=6)

        tk.Label(
            bar, text="AgentCode v2.1", font=FONTS["small"],
            bg=COLORS["bg_panel"], fg=COLORS["text_dim"]
        ).pack(side=tk.LEFT, padx=0)

        # Status indicator
        self._status_label = tk.Label(
            bar, text="Memuat...", font=FONTS["small"],
            bg=COLORS["bg_panel"], fg=COLORS["accent4"]
        )
        self._status_label.pack(side=tk.RIGHT, padx=16)

        # Theme separator
        tk.Frame(bar, bg=COLORS["border"], height=1).pack(side=tk.BOTTOM, fill=tk.X)

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=COLORS["bg_panel"], width=210)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=COLORS["border"], width=1).pack(side=tk.RIGHT, fill=tk.Y)

        # Section: Quick Commands
        tk.Label(
            sidebar, text="QUICK COMMANDS", font=FONTS["tiny"],
            bg=COLORS["bg_panel"], fg=COLORS["text_dim"]
        ).pack(anchor=tk.W, padx=14, pady=(14, 4))

        quick_cmds = [
            ("Buat File",    "buat file "),
            ("Edit File",   "edit file "),
            ("Berita",       "cari berita terbaru teknologi"),
            ("Cari Web",     "cari informasi tentang "),
            ("Riset Topik",  "riset tentang "),
            ("Download",    "download "),
            ("List Files",   "tampilkan daftar file"),
            ("Status",       "tampilkan statistik"),
            ("Waktu",        "jam berapa sekarang"),
        ]

        for label, cmd in quick_cmds:
            btn = tk.Button(
                sidebar, text=label, font=FONTS["small"],
                bg=COLORS["bg_panel"], fg=COLORS["text"],
                activebackground=COLORS["bg_input"],
                activeforeground=COLORS["accent"],
                relief="flat", cursor="hand2",
                anchor="w", padx=14,
                command=lambda c=cmd: self._quick_insert(c)
            )
            btn.pack(fill=tk.X, pady=1)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS["bg_input"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLORS["bg_panel"]))

        # Section: Workspace
        tk.Frame(sidebar, bg=COLORS["border"], height=1).pack(fill=tk.X, padx=10, pady=8)
        tk.Label(
            sidebar, text="WORKSPACE", font=FONTS["tiny"],
            bg=COLORS["bg_panel"], fg=COLORS["text_dim"]
        ).pack(anchor=tk.W, padx=14, pady=(0, 4))

        ws_path = ROOT / "workspace"
        try:
            files = [f.name for f in ws_path.iterdir() if f.is_file()][:10]
        except Exception:
            files = []

        for fname in files:
            tk.Button(
                sidebar, text=f"  {fname}", font=FONTS["tiny"],
                bg=COLORS["bg_panel"], fg=COLORS["text_dim"],
                activebackground=COLORS["bg_input"],
                relief="flat", cursor="hand2", anchor="w",
                command=lambda fn=fname: self._quick_insert(f"tampilkan isi file {fn}")
            ).pack(fill=tk.X, pady=0)

        # Clear chat btn (bottom)
        tk.Button(
            sidebar, text="🗑 Bersihkan Chat", font=FONTS["small"],
            bg=COLORS["bg_panel"], fg=COLORS["accent3"],
            activebackground="#2d1b1b", relief="flat", cursor="hand2",
            command=self._clear_chat
        ).pack(side=tk.BOTTOM, fill=tk.X, padx=4, pady=8)

    def _build_chat_area(self, parent):
        chat_frame = tk.Frame(parent, bg=COLORS["bg"])
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Chat scrollbox
        self.chat_box = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=FONTS["body"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            relief="flat",
            padx=20, pady=12,
            state=tk.DISABLED,
            cursor="arrow",
        )
        self.chat_box.pack(fill=tk.BOTH, expand=True)

        # Tags
        self.chat_box.tag_configure("user_tag",   foreground=COLORS["accent"],  font=FONTS["header"])
        self.chat_box.tag_configure("ai_tag",      foreground=COLORS["accent2"], font=FONTS["header"])
        self.chat_box.tag_configure("error_tag",   foreground=COLORS["accent3"])
        self.chat_box.tag_configure("success_tag", foreground=COLORS["accent2"])
        self.chat_box.tag_configure("code_tag",    font=FONTS["code"], foreground="#d2a8ff")
        self.chat_box.tag_configure("dim_tag",     foreground=COLORS["text_dim"], font=FONTS["small"])
        self.chat_box.tag_configure("time_tag",    foreground=COLORS["text_dim"], font=FONTS["tiny"])

        # Welcome message
        self._append_chat(
            "KokoAI",
            "Halo! Saya KokoAI 2.1 — Asisten coding lokal Anda.\n"
            "Engine sedang dimuat, harap tunggu sebentar...\n\n"
            "💡 Gunakan quick commands di sidebar kiri\n"
            "⌨️  Atau ketikkan perintah bebas di bawah",
            tag="ai_tag"
        )

    def _build_input_bar(self):
        bar = tk.Frame(self.root, bg=COLORS["bg_panel"])
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Frame(bar, bg=COLORS["border"], height=1).pack(fill=tk.X)

        inner = tk.Frame(bar, bg=COLORS["bg_panel"], pady=10, padx=12)
        inner.pack(fill=tk.X)

        # Input text
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            inner,
            textvariable=self.input_var,
            font=FONTS["body"],
            bg=COLORS["bg_input"],
            fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            relief="flat",
            bd=0, highlightthickness=2,
            highlightcolor=COLORS["accent"],
            highlightbackground=COLORS["border"],
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        self.input_entry.bind("<Return>", self._on_send)
        self.input_entry.bind("<Up>",     self._history_up)
        self.input_entry.bind("<Down>",   self._history_down)
        self._hist_idx = -1

        # Send button
        self.send_btn = tk.Button(
            inner, text="Kirim  ▶", font=FONTS["body"],
            bg=COLORS["accent"], fg="#ffffff",
            activebackground=COLORS["hover"],
            relief="flat", cursor="hand2",
            padx=16, pady=6,
            command=self._on_send
        )
        self.send_btn.pack(side=tk.LEFT)

        # Attach file button
        tk.Button(
            inner, text="📎", font=FONTS["body"],
            bg=COLORS["bg_input"], fg=COLORS["text_dim"],
            activebackground=COLORS["bg_input"],
            relief="flat", cursor="hand2",
            padx=8, pady=6,
            command=self._attach_file
        ).pack(side=tk.LEFT, padx=(4, 0))

        # Hint
        tk.Label(
            bar, text="↑↓ history • Enter kirim • Ctrl+L bersihkan",
            font=FONTS["tiny"], bg=COLORS["bg_panel"], fg=COLORS["text_dim"]
        ).pack(pady=(0, 4))

        self.root.bind("<Control-l>", lambda e: self._clear_chat())
        self.input_entry.focus_set()

    # ── Core Logic ────────────────────────────────────────────────

    def _on_send(self, event=None):
        text = self.input_var.get().strip()
        if not text or self._thinking:
            return

        self.input_var.set("")
        self._history.insert(0, text)
        self._hist_idx = -1

        self._append_chat("Anda", text, tag="user_tag")
        self._thinking = True
        self.send_btn.config(state=tk.DISABLED, text="Menunggu...")
        self._set_status("KokoAI sedang berpikir...", COLORS["accent4"])

        t = threading.Thread(target=self._process_input, args=(text,), daemon=True)
        t.start()

    def _process_input(self, text):
        try:
            if self._engine is None:
                self._response_queue.put(("ai", "Engine belum selesai dimuat. Harap tunggu...", None))
                return
            response = self._engine.process(text)
            resp_text = response.get("text", "") if isinstance(response, dict) else str(response)
            resp_type = response.get("type", "info") if isinstance(response, dict) else "info"
            provider  = response.get("provider", "") if isinstance(response, dict) else ""
            self._response_queue.put(("ai", resp_text, resp_type, provider))
        except Exception as e:
            self._response_queue.put(("ai", f"Error: {e}", "error", ""))

    def _poll_queue(self):
        """Poll result queue from background threads."""
        try:
            while True:
                item = self._response_queue.get_nowait()
                if item[0] == "status":
                    _, msg, color = item
                    self._set_status(msg, color)
                elif item[0] == "ai":
                    _, text, *rest = item
                    resp_type = rest[0] if rest else "info"
                    provider  = rest[1] if len(rest) > 1 else ""
                    tag = "error_tag" if resp_type == "error" else "success_tag" if resp_type == "success" else "ai_tag"
                    suffix = f" [via {provider}]" if provider and provider != "local" else ""
                    self._append_chat(f"KokoAI{suffix}", text, tag=tag)
                    self._thinking = False
                    self.send_btn.config(state=tk.NORMAL, text="Kirim  ▶")
                    self._set_status("Siap", COLORS["accent2"])
        except queue.Empty:
            pass
        self.root.after(50, self._poll_queue)

    # ── Chat helpers ──────────────────────────────────────────────

    def _append_chat(self, sender, text, tag="ai_tag"):
        self.chat_box.config(state=tk.NORMAL)
        now = datetime.datetime.now().strftime("%H:%M")

        self.chat_box.insert(tk.END, f"\n{sender}  ", tag)
        self.chat_box.insert(tk.END, f"[{now}]\n", "time_tag")

        # Detect code blocks
        if "```" in text:
            parts = text.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:  # code block
                    lines = part.strip().split("\n")
                    # skip language hint line
                    code_text = "\n".join(lines[1:] if lines[0].isalpha() else lines)
                    self.chat_box.insert(tk.END, code_text + "\n", "code_tag")
                else:
                    self.chat_box.insert(tk.END, part)
        else:
            self.chat_box.insert(tk.END, text + "\n")

        self.chat_box.insert(tk.END, "\n")
        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)

    def _clear_chat(self):
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.delete("1.0", tk.END)
        self.chat_box.config(state=tk.DISABLED)

    def _quick_insert(self, text):
        self.input_var.set(text)
        self.input_entry.focus_set()
        self.input_entry.icursor(tk.END)

    def _attach_file(self):
        path = filedialog.askopenfilename(
            title="Pilih file untuk dibaca KokoAI",
            filetypes=[("All files", "*.*"), ("Python", "*.py"), ("HTML", "*.html")]
        )
        if path:
            fname = os.path.basename(path)
            self.input_var.set(f"baca file {fname}")
            self.input_entry.focus_set()

    def _set_status(self, text, color=None):
        self._status_label.config(
            text=text,
            fg=color or COLORS["text_dim"]
        )

    def _history_up(self, event=None):
        if self._hist_idx < len(self._history) - 1:
            self._hist_idx += 1
            self.input_var.set(self._history[self._hist_idx])
            self.input_entry.icursor(tk.END)

    def _history_down(self, event=None):
        if self._hist_idx > 0:
            self._hist_idx -= 1
            self.input_var.set(self._history[self._hist_idx])
        elif self._hist_idx == 0:
            self._hist_idx = -1
            self.input_var.set("")


def main():
    root = tk.Tk()
    root.tk.call("tk", "scaling", 1.3)
    try:
        """Set dark title bar on Windows 11."""
        from ctypes import windll, byref, sizeof, c_int
        hwnd = int(root.wm_frame(), 16)
        value = c_int(2)
        windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(value), sizeof(value))
    except Exception:
        pass

    app = KokoAIGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
