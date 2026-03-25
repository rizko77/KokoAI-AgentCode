import re
import requests
from bs4 import BeautifulSoup
from config.settings import USER_AGENT, REQUEST_TIMEOUT, WEB_SOURCES


# =====================================================
# Security: URL whitelist & unsafe content filtering
# =====================================================
BLOCKED_DOMAINS = [
    "malware", "phishing", "hack", "exploit", "crack",
    "torrent", "piracy", "warez",
]

UNSAFE_CODE_PATTERNS = [
    "os.system", "subprocess.call", "subprocess.run", "subprocess.Popen",
    "rm -rf", "eval(", "exec(", "shutil.rmtree", "os.remove",
    "os.unlink", "child_process", "__import__", "exec.Command",
    "drop table", "chmod 777", "curl | bash", "wget | sh",
    "powershell -enc", "invoke-expression", "system(",
    "Runtime.exec", "ProcessBuilder", "cmd.exe /c",
]


def _is_url_safe(url):
    """Check if URL is safe to scrape."""
    url_lower = url.lower()
    for blocked in BLOCKED_DOMAINS:
        if blocked in url_lower:
            return False
    return True


def _is_valid_code(code, language="python"):
    """Validate code snippet is real code and not malicious."""
    if not code or len(code.strip()) < 20:
        return False
    if len(code) > 50000:
        return False

    code_lower = code.lower()
    for pattern in UNSAFE_CODE_PATTERNS:
        if pattern.lower() in code_lower:
            return False

    code_indicators = ["=", "(", ")", "{", "}", ";", ":", "def ", "class ",
                       "function ", "var ", "let ", "const ", "import ",
                       "if ", "for ", "while ", "return "]
    indicator_count = sum(1 for ind in code_indicators if ind in code)
    return indicator_count >= 2


# =====================================================
# Scrapy-based deep scraper (for complex sites)
# =====================================================
def scrape_with_scrapy(url, max_pages=3):
    """Use Scrapy to deeply scrape a website for content."""
    try:
        import scrapy
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings
        import tempfile
        import json

        if not _is_url_safe(url):
            return {"error": "URL terdeteksi tidak aman."}

        results = []

        class ContentSpider(scrapy.Spider):
            name = "content_spider"
            start_urls = [url]
            custom_settings = {
                "LOG_ENABLED": False,
                "ROBOTSTXT_OBEY": True,
                "DOWNLOAD_TIMEOUT": REQUEST_TIMEOUT,
                "USER_AGENT": USER_AGENT,
                "CLOSESPIDER_PAGECOUNT": max_pages,
                "DEPTH_LIMIT": 1,
            }

            def parse(self, response):
                title = response.css("title::text").get("").strip()
                paragraphs = response.css("p::text, article p::text, main p::text").getall()
                code_blocks = response.css("pre code::text, pre::text, .highlight pre::text").getall()

                clean_paras = [p.strip() for p in paragraphs if len(p.strip()) > 30]
                clean_codes = [c.strip() for c in code_blocks if _is_valid_code(c.strip())]

                results.append({
                    "url": response.url,
                    "title": title,
                    "content": clean_paras[:10],
                    "code_snippets": clean_codes[:5],
                })

        process = CrawlerProcess({"LOG_ENABLED": False})
        process.crawl(ContentSpider)
        process.start(stop_after_crawl=True)

        return results

    except Exception as e:
        return {"error": f"Scrapy error: {e}"}


# =====================================================
# BeautifulSoup-based scraper (fast, for single pages)
# =====================================================
def scrape_code_snippets(url, language="python"):
    """Extract code snippets from a webpage."""
    if not _is_url_safe(url):
        return []

    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        snippets = []

        selectors = [
            "pre code", "pre.code", "code.highlight",
            "pre", ".highlight pre", ".blob-code-inner",
            ".s-code-block", ".prettyprint",
        ]

        for selector in selectors:
            for elem in soup.select(selector):
                code = elem.get_text().strip()
                if code and _is_valid_code(code, language) and code not in snippets:
                    snippets.append(code)

        for code_elem in soup.select("code"):
            code = code_elem.get_text().strip()
            if len(code) > 50 and _is_valid_code(code, language) and code not in snippets:
                snippets.append(code)

        return snippets

    except Exception:
        return []


def scrape_page_text(url):
    """Extract main text content from a webpage."""
    if not _is_url_safe(url):
        return ""

    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        main = soup.select_one("main, article, .content, .post-body, #content")
        if main:
            text = main.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        text = re.sub(r'\n{3,}', '\n\n', text)
        return text[:10000]

    except Exception:
        return ""


def summarize_article(url):
    """Extract and summarize an article from a URL."""
    if not _is_url_safe(url):
        return {"error": "URL terdeteksi tidak aman."}

    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title else "Informasi Artikel"
        main = soup.select_one("main, article, .content, .post-body, #content")

        if main:
            paragraphs = main.select("p")
        else:
            paragraphs = soup.select("p")

        content_lines = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 40:
                content_lines.append(text)

        if not content_lines:
            return {"error": "Tidak bisa mengekstrak isi artikel dari halaman tersebut."}

        # NLTK-enhanced extractive summary
        summary = _extractive_summary(content_lines)

        return {
            "title": title,
            "summary": summary,
            "url": url,
            "source_lines": len(content_lines)
        }

    except Exception as e:
        return {"error": str(e)}


def _extractive_summary(paragraphs, max_sentences=5):
    """Generate an extractive summary using NLTK sentence tokenization."""
    try:
        from nltk.tokenize import sent_tokenize
        all_text = " ".join(paragraphs)
        sentences = sent_tokenize(all_text)

        if len(sentences) <= max_sentences:
            return "\n- ".join(sentences)

        # Score sentences by position and length
        scored = []
        for i, sent in enumerate(sentences):
            score = len(sent.split())  # word count
            if i < 3:
                score += 20  # boost early sentences
            if i == len(sentences) - 1:
                score += 10  # boost conclusion
            scored.append((score, sent))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [s[1] for s in scored[:max_sentences]]
        return "\n- ".join(top)

    except Exception:
        summary = "\n- ".join(paragraphs[:3])
        if len(paragraphs) > 3:
            summary += "\n- " + paragraphs[len(paragraphs) // 2]
        return summary


# =====================================================
# Smart search across known web sources
# =====================================================
def search_known_sources(query, max_results=5):
    """Search across stored WEB_SOURCES for relevant content."""
    results = []

    # Determine which sources are relevant based on query
    query_lower = query.lower()
    source_priority = []

    if any(w in query_lower for w in ("berita", "news", "terkini", "terbaru")):
        source_priority = ["news_google", "google", "yahoo"]
    elif any(w in query_lower for w in ("code", "kode", "programming", "coding")):
        source_priority = ["stackoverflow", "github", "w3schools"]
    elif any(w in query_lower for w in ("tutorial", "belajar", "learn")):
        source_priority = ["w3schools", "petanikode", "dicoding"]
    elif any(w in query_lower for w in ("tailwind", "css", "style", "desain")):
        source_priority = ["tailwindcss", "w3schools"]
    elif any(w in query_lower for w in ("laravel", "php")):
        source_priority = ["laravel", "stackoverflow"]
    else:
        source_priority = ["google", "stackoverflow", "w3schools"]

    for source_key in source_priority[:3]:
        base_url = WEB_SOURCES.get(source_key, "")
        if not base_url:
            continue

        try:
            page_text = scrape_page_text(base_url)
            if page_text:
                results.append({
                    "source": source_key,
                    "url": base_url,
                    "content": page_text[:500],
                })
        except Exception:
            continue

    return results


def extract_code_from_text(text, language="python"):
    """Extract code blocks from markdown-like text."""
    snippets = []

    pattern = rf'```(?:{language})?\s*\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    for match in matches:
        code = match.strip()
        if _is_valid_code(code, language):
            snippets.append(code)

    lines = text.split("\n")
    code_block = []
    in_block = False

    for line in lines:
        if line.startswith("    ") or line.startswith("\t"):
            code_block.append(line.strip())
            in_block = True
        elif in_block and line.strip() == "":
            code_block.append("")
        elif in_block:
            code = "\n".join(code_block).strip()
            if _is_valid_code(code, language):
                snippets.append(code)
            code_block = []
            in_block = False

    if code_block:
        code = "\n".join(code_block).strip()
        if _is_valid_code(code, language):
            snippets.append(code)

    return snippets
