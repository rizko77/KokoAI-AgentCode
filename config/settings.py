import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "./workspace")).resolve()
DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()

DATA_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"
MODEL_STATE_FILE = DATA_DIR / "model_state.json"
TRAINING_LOG_FILE = DATA_DIR / "training_log.json"
CONVERSATION_FILE = DATA_DIR / "conversation.json"

NGRAM_SIZE = int(os.getenv("NGRAM_SIZE", "3"))
MAX_SUGGESTIONS = int(os.getenv("MAX_SUGGESTIONS", "5"))
TRAINING_INTERVAL = int(os.getenv("TRAINING_INTERVAL", "60"))
AUTO_LEARN = os.getenv("AUTO_LEARN", "true").lower() == "true"
AUTO_SCHEDULER = os.getenv("AUTO_SCHEDULER", "true").lower() == "true"

SEARCH_ENGINE = os.getenv("SEARCH_ENGINE", "duckduckgo")
MAX_SCRAPE_PAGES = int(os.getenv("MAX_SCRAPE_PAGES", "10"))
REQUEST_TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

WEB_SOURCES = {
    "google": "https://www.google.com/?hl=ID",
    "yahoo": "https://id.yahoo.com/",
    "yandex": "https://yandex.com/",
    "github": "https://github.com/",
    "stackoverflow": "https://stackoverflow.com/",
    "petanikode": "https://www.petanikode.com/",
    "w3schools": "https://www.w3schools.com/",
    "tailwindcss": "https://tailwindcss.com/",
    "microsoft": "https://www.microsoft.com/id-id",
    "opensource": "https://opensource.com/",
    "dicoding": "https://www.dicoding.com/",
    "youtube": "https://www.youtube.com/",
    "tiktok": "https://www.tiktok.com/id-ID/",
    "news_google": "https://news.google.com/",
    "laravel": "https://laravel.com/",
}

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".html": "html",
    ".css": "css",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".dart": "dart",
    ".sql": "sql",
    ".sh": "bash",
    ".bat": "batch",
    ".ps1": "powershell",
    ".json": "json",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".txt": "text",
}

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# === AI Provider API Keys ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_PROVIDER_PRIORITY = os.getenv("AI_PROVIDER_PRIORITY", "local,gemini,claude,openai")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-20241022")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Set env vars so API clients can read them
if GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
if CLAUDE_API_KEY:
    os.environ["CLAUDE_API_KEY"] = CLAUDE_API_KEY
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

VERSION = "2.1"
BUILD = "2.10.25032026"
APP_NAME = "KokoAI 2.1 - AgentCode"
AUTHOR = "Rizko Imsar, KokoDev Studio"
