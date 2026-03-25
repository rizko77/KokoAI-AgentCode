"""
KokoAI - AI Provider Router
Memilih AI provider terbaik yang tersedia: Gemini → Claude → OpenAI → Local Brain
"""
import os
import sys

# Tambah root path agar import bisa jalan
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AIRouter:
    """
    Smart AI router yang memilih provider terbaik berdasarkan:
    1. Ketersediaan API key
    2. Jenis task
    3. Prioritas yang dikonfigurasi di .env
    """

    PROVIDERS = ["local", "gemini", "claude", "openai"]

    def __init__(self):
        self._gemini = None
        self._claude = None
        self._openai = None
        self._available = []
        self._detect_providers()

    def _detect_providers(self):
        """Detect which providers are available based on API keys."""
        self._available = []

        if os.getenv("GEMINI_API_KEY"):
            try:
                from api.gemini_api import client as gemini_client
                self._gemini = gemini_client
                self._available.append("gemini")
            except Exception:
                pass

        if os.getenv("CLAUDE_API_KEY"):
            try:
                from api.claude_api import client as claude_client
                self._claude = claude_client
                self._available.append("claude")
            except Exception:
                pass

        if os.getenv("OPENAI_API_KEY"):
            try:
                from api.openai_api import client as openai_client
                self._openai = openai_client
                self._available.append("openai")
            except Exception:
                pass

        self._available.append("local")

    def get_available_providers(self):
        return self._available.copy()

    def get_primary_provider(self):
        """Get the best available provider."""
        priority = os.getenv("AI_PROVIDER_PRIORITY", "gemini,claude,openai,local")
        order = [p.strip() for p in priority.split(",")]
        for p in order:
            if p in self._available:
                return p
        return "local"

    def chat(self, prompt, task_type="general", context="", local_engine=None):
        """
        Route a prompt to the best available AI provider.
        Falls back to local engine N-gram suggestions if no API key.
        
        Returns: (response_text, provider_used)
        """
        provider = self.get_primary_provider()

        # — Gemini —
        if provider == "gemini" and self._gemini:
            model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            if task_type == "code":
                result = self._gemini.generate_code(prompt, model=model)
            elif task_type == "explain":
                result = self._gemini.explain_code(prompt, model=model)
            else:
                result = self._gemini.answer_question(prompt, context=context, model=model)
            if result:
                return result, "gemini"

        # — Claude —
        if provider == "claude" and self._claude:
            model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
            if task_type == "code":
                result = self._claude.generate_code(prompt, model=model)
            elif task_type == "explain":
                result = self._claude.explain_code(prompt, model=model)
            else:
                result = self._claude.answer_question(prompt, context=context, model=model)
            if result:
                return result, "claude"

        # — OpenAI —
        if provider == "openai" and self._openai:
            model = os.getenv("OPENAI_MODEL", "gpt-4o")
            result = self._openai.chat(prompt, model=model)
            if result:
                return result, "openai"

        # — Local fallback —
        if local_engine:
            suggestions = local_engine.get_suggestions(prompt)
            if suggestions:
                lines = [f"  {t}" for t, _ in suggestions[:5]]
                return "Suggestion lokal:\n" + "\n".join(lines), "local"
            return "Belum ada model yang bisa menjawab ini. Coba training dulu atau tambahkan API key di .env", "local"

        return "Tidak ada provider AI yang aktif.", "none"

    def generate_code(self, description, language="python", local_engine=None):
        """Generate code dengan provider terbaik."""
        prompt = f"Buatkan kode {language} untuk: {description}"
        return self.chat(prompt, task_type="code", local_engine=local_engine)

    def generate_file_content(self, filename, description, language="python", local_engine=None):
        """Generate full file content menggunakan AI provider."""
        prompt = (
            f"Buatkan isi file lengkap untuk file bernama '{filename}' ({language}).\n"
            f"Deskripsi: {description}\n"
            f"Berikan HANYA kode lengkap yang siap digunakan, tanpa penjelasan di luar kode."
        )
        return self.chat(prompt, task_type="code", local_engine=local_engine)

    def explain(self, code_or_text, local_engine=None):
        """Explain code atau teks."""
        return self.chat(code_or_text, task_type="explain", local_engine=local_engine)

    def answer(self, question, context="", local_engine=None):
        """Answer a general question."""
        return self.chat(question, task_type="general", context=context, local_engine=local_engine)

    def status(self):
        """Return provider status info."""
        lines = []
        for p in self.PROVIDERS:
            if p in self._available:
                tag = "AKTIF" if p == self.get_primary_provider() else "tersedia"
                lines.append(f"  [{tag.upper()}] {p.capitalize()}")
            else:
                lines.append(f"  [OFF]  {p.capitalize()} (tidak ada API key)")
        return "\n".join(lines)


# Singleton instance
_router = None


def get_router():
    global _router
    if _router is None:
        _router = AIRouter()
    return _router
