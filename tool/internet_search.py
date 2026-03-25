"""
KokoAI - Internet Search Engine
Primary: Google Search (via scraping)
Fallback: Wikipedia, StackOverflow API, Google News RSS
Slow-net friendly: aggressive timeouts, retry, compression
"""
import re
import time
import urllib3
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from config.settings import USER_AGENT, REQUEST_TIMEOUT, MAX_SCRAPE_PAGES
except ImportError:
    USER_AGENT = "Mozilla/5.0 (compatible; KokoAI/2.1)"
    REQUEST_TIMEOUT = 10
    MAX_SCRAPE_PAGES = 10


# ── Slow-net friendly session ─────────────────────────────────────────
def _make_session(slow_net=False):
    """Create a requests Session optimized for slow connections."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })
    adapter = requests.adapters.HTTPAdapter(
        max_retries=urllib3.util.retry.Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _safe_get(url, timeout=None, slow=False, **kwargs):
    """GET with retry, slow-net support, and safe error handling."""
    t = timeout or (20 if slow else REQUEST_TIMEOUT)
    session = _make_session(slow_net=slow)
    try:
        resp = session.get(url, timeout=t, verify=False, **kwargs)
        resp.raise_for_status()
        return resp
    except requests.exceptions.Timeout:
        # On timeout, retry once with doubled timeout
        try:
            resp = session.get(url, timeout=t * 2, verify=False, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception:
            return None
    except Exception:
        return None


# ── Google Search (primary) ───────────────────────────────────────────
def search_google(query, max_results=5, slow=False):
    """
    Scrape Google search results.
    Primary search engine for KokoAI.
    """
    try:
        encoded = quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}&hl=id&num={max_results + 3}&safe=active"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
        }
        resp = _safe_get(url, slow=slow, headers=headers)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        # Google result blocks: div.g, div[data-sokoban-*], etc.
        for block in soup.select("div.g, div[data-hveid]"):
            title_el = block.select_one("h3")
            url_el = block.select_one("a[href]")
            snippet_el = block.select_one("div[data-sncf], span.aCOpRe, div.VwiC3b, div[style] > span")

            if not title_el or not url_el:
                continue

            title = title_el.get_text(strip=True)
            href = url_el.get("href", "")
            if href.startswith("/url?q="):
                href = href.split("/url?q=")[1].split("&")[0]
            if not href.startswith("http"):
                continue

            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

            results.append({
                "title": title,
                "snippet": snippet[:300],
                "url": href,
                "source": "google",
            })
            if len(results) >= max_results:
                break

        return results
    except Exception:
        return []


# ── Google News RSS ───────────────────────────────────────────────────
def search_news(query, max_results=5, slow=False):
    """Search news via Google News RSS (no API key needed)."""
    try:
        encoded = quote_plus(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=id&gl=ID&ceid=ID:id"

        resp = _safe_get(url, slow=slow)
        if not resp:
            return []

        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
        results = []

        for item in items[:max_results]:
            title = item.title.text if item.title else "Berita"
            link = item.link.text if item.link else ""
            pub_date = item.pubDate.text if item.pubDate else ""
            source_el = item.find("source")
            source_name = source_el.text if source_el else "Google News"

            results.append({
                "title": title,
                "snippet": f"{source_name} - {pub_date}",
                "url": link,
                "source": "google_news",
                "date": pub_date,
            })

        return results
    except Exception:
        return []


# ── Wikipedia fallback ────────────────────────────────────────────────
def search_wikipedia(query, max_results=5, lang="id", slow=False):
    """Search Wikipedia (Indonesian first, then English)."""
    try:
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "utf8": "",
            "format": "json",
            "srlimit": max_results,
        }
        resp = _safe_get(url, slow=slow, params=params)
        if not resp:
            return []

        data = resp.json()
        results = []
        for item in data.get("query", {}).get("search", [])[:max_results]:
            snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
            title = item.get("title", "")
            link = f"https://{lang}.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
            results.append({
                "title": title,
                "snippet": snippet + "...",
                "url": link,
                "source": "wikipedia",
            })
        return results
    except Exception:
        return []


# ── StackOverflow ─────────────────────────────────────────────────────
def search_code(query, language="python", max_results=5, slow=False):
    """Search code on StackOverflow API + Google fallback."""
    results = []
    try:
        url = "https://api.stackexchange.com/2.3/search/advanced"
        params = {
            "order": "desc",
            "sort": "relevance",
            "q": query,
            "tagged": language,
            "site": "stackoverflow",
            "pagesize": max_results,
        }
        resp = _safe_get(url, slow=slow, params=params)
        if resp:
            data = resp.json()
            for item in data.get("items", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": f"StackOverflow - {item.get('score', 0)} votes, {item.get('answer_count', 0)} answers",
                    "url": item.get("link", ""),
                    "source": "stackoverflow",
                })
    except Exception:
        pass

    if not results:
        # Fallback: Google search with code context
        google_results = search_google(f"{language} {query} site:stackoverflow.com OR site:github.com", max_results, slow=slow)
        results.extend(google_results)

    return results


# ── Unified web search ────────────────────────────────────────────────
def search_web(query, max_results=5, slow=False):
    """
    Smart web search router:
    - News queries → Google News RSS
    - Code queries → StackOverflow + Google
    - General info → Google primary, Wikipedia fallback
    """
    query_lower = query.lower()

    # Strip time suffixes that were added
    clean_query = re.sub(r'\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$', '', query, flags=re.IGNORECASE).strip()
    clean_query = re.sub(r'\s+\d{4}$', '', clean_query).strip()

    # Route by query type
    is_news = any(w in query_lower for w in ("berita", "news", "terkini", "terbaru", "hari ini", "today", "breaking"))
    is_code = any(w in query_lower for w in ("code", "kode", "programming", "script", "fungsi", "function", "error", "bug"))

    results = []

    if is_news:
        results = search_news(clean_query, max_results, slow=slow)
        if not results:
            results = search_google(clean_query + " berita terbaru", max_results, slow=slow)
    elif is_code:
        results = search_code(clean_query, max_results=max_results, slow=slow)
    else:
        # Primary: Google
        results = search_google(clean_query, max_results, slow=slow)
        # Fallback: Wikipedia
        if len(results) < 2:
            wiki = search_wikipedia(clean_query, max_results, slow=slow)
            results.extend(wiki)

    return results if results else [{"error": "Tidak ada hasil ditemukan."}]


def search_documentation(query, language="python", slow=False):
    """Search documentation for a specific language/framework."""
    return search_web(f"{language} {query} documentation tutorial", 3, slow=slow)
