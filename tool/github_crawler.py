"""
KokoAI - GitHub Web Scraper
Menjelajahi github.com secara langsung (no API, no token needed).

Etika scraping:
- Gunakan User-Agent yang jujur
- Selalu pakai time.sleep() antar request
- Jangan crawl lebih dari yang diperlukan
- Hormati robots.txt (GitHub memperbolehkan scraping halaman publik)
"""
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus, urlparse

try:
    from config.settings import REQUEST_TIMEOUT
except ImportError:
    REQUEST_TIMEOUT = 12

# ── Browser-like headers ──────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Etika: jeda antar request (detik)
_MIN_SLEEP = 1.2
_MAX_SLEEP = 2.8


def _polite_sleep():
    """Jeda random agar tidak membebani server GitHub."""
    time.sleep(random.uniform(_MIN_SLEEP, _MAX_SLEEP))


def _safe_get(url, timeout=None, retries=2):
    """GET dengan retry dan error handling yang aman."""
    t = timeout or REQUEST_TIMEOUT
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=t, allow_redirects=True)
            if resp.status_code == 429:          # Rate limit
                time.sleep(10 + attempt * 5)
                continue
            if resp.status_code in (403, 451):   # Blocked / Legal
                return None
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(3)
            continue
        except Exception:
            return None
    return None


# ── 1. Search Repos ───────────────────────────────────────────────────

def search_github_repos(query, language="python", max_results=5, since=None):
    """
    Scrape halaman pencarian GitHub untuk mencari repository.
    URL: https://github.com/search?q=...&type=repositories
    """
    results = []
    try:
        lang_part = f"+language%3A{language}" if language else ""
        encoded_q = quote_plus(query) + lang_part
        url = f"https://github.com/search?q={encoded_q}&type=repositories&s=stars&o=desc"

        resp = _safe_get(url)
        if not resp:
            return results

        soup = BeautifulSoup(resp.text, "lxml")

        # GitHub search result items
        # Selector untuk halaman pencarian GitHub (versi React dan versi lama)
        repo_items = soup.select("div[data-testid='results-list'] > div") or \
                     soup.select("li.repo-list-item") or \
                     soup.select("div.search-result")

        # Fallback: cari semua link yang pola-nya adalah /owner/repo
        if not repo_items:
            repo_items = _extract_from_raw_html(soup, max_results)
            return repo_items[:max_results]

        for item in repo_items[:max_results]:
            result = _parse_repo_item(item, soup)
            if result:
                results.append(result)

    except Exception:
        pass

    # Fallback jika selector tidak cocok (GitHub sering ubah HTML)
    if not results:
        results = _search_repos_fallback(query, language, max_results)

    _polite_sleep()
    return results[:max_results]


def _parse_repo_item(item, soup):
    """Parse satu item repo dari halaman search."""
    try:
        # Cari link utama repo
        link = item.find("a", href=re.compile(r"^/[^/]+/[^/]+$"))
        if not link:
            return None

        href = link.get("href", "")
        # Pastikan ini repo link, bukan navigasi
        parts = href.strip("/").split("/")
        if len(parts) != 2:
            return None

        owner, repo_name = parts
        # Skip GitHub internal pages
        if owner in ("about", "topics", "collections", "trending", "explore", "login"):
            return None

        full_name = f"{owner}/{repo_name}"
        repo_url = f"https://github.com/{full_name}"

        # Deskripsi
        desc_el = item.find("p") or item.find("[data-testid='search-result-description']")
        description = desc_el.get_text(strip=True) if desc_el else ""

        # Bintang
        stars = "0"
        star_patterns = [
            item.find("a", href=re.compile(r"/stargazers")),
            item.find(string=re.compile(r"\d+\.?\d*k?", re.I)),
        ]
        for sp in star_patterns:
            if sp:
                text = sp.get_text(strip=True) if hasattr(sp, "get_text") else str(sp)
                if re.search(r"\d", text):
                    stars = text.strip()
                    break

        # Bahasa
        lang_el = item.find("span", itemprop="programmingLanguage") or \
                  item.find("span", attrs={"data-testid": "language"})
        lang = lang_el.get_text(strip=True) if lang_el else ""

        return {
            "name": full_name,
            "description": description[:200],
            "url": repo_url,
            "stars": stars,
            "language": lang,
            "owner": owner,
            "repo": repo_name,
        }
    except Exception:
        return None


def _extract_from_raw_html(soup, max_results):
    """Fallback: ekstrak repo links dari raw HTML."""
    results = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not re.match(r"^/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", href):
            continue

        parts = href.strip("/").split("/")
        if len(parts) != 2:
            continue

        owner, repo_name = parts
        if owner in ("about", "topics", "collections", "trending", "explore",
                     "login", "signup", "pricing", "features", "enterprise"):
            continue

        key = f"{owner}/{repo_name}"
        if key in seen:
            continue
        seen.add(key)

        results.append({
            "name": key,
            "description": a.get_text(strip=True)[:100],
            "url": f"https://github.com/{key}",
            "stars": "?",
            "language": "",
            "owner": owner,
            "repo": repo_name,
        })

        if len(results) >= max_results:
            break

    return results


def _search_repos_fallback(query, language, max_results):
    """
    Fallback: cari repo via GitHub Topics atau Trending.
    Dipakai jika halaman search berubah strukturnya.
    """
    results = []
    try:
        # Coba via Google dengan site:github.com
        from tool.internet_search import search_google
        google_results = search_google(
            f"{query} {language} site:github.com",
            max_results=max_results + 3,
        )
        for r in google_results:
            url = r.get("url", "")
            m = re.match(r"https://github\.com/([^/]+)/([^/?\s]+)", url)
            if m:
                owner, repo = m.group(1), m.group(2)
                if owner not in ("topics", "trending", "explore"):
                    results.append({
                        "name": f"{owner}/{repo}",
                        "description": r.get("snippet", "")[:200],
                        "url": f"https://github.com/{owner}/{repo}",
                        "stars": "?",
                        "language": language,
                        "owner": owner,
                        "repo": repo,
                    })
    except Exception:
        pass
    return results[:max_results]


# ── 2. Search Code Files ──────────────────────────────────────────────

def search_github_code(query, language="python", max_results=5):
    """
    Scrape halaman GitHub Code Search.
    URL: https://github.com/search?q=...&type=code
    """
    results = []
    try:
        lang_part = f"+language%3A{language}" if language else ""
        encoded_q = quote_plus(query) + lang_part
        url = f"https://github.com/search?q={encoded_q}&type=code"

        resp = _safe_get(url)
        if not resp:
            return results

        soup = BeautifulSoup(resp.text, "lxml")

        # Cari semua link ke file kode (pola: /owner/repo/blob/branch/path)
        seen = set()
        for a in soup.find_all("a", href=re.compile(r"^/[^/]+/[^/]+/blob/")):
            href = a.get("href", "")
            if href in seen:
                continue
            seen.add(href)

            # Parse href: /owner/repo/blob/branch/path/to/file.py
            parts = href.strip("/").split("/", 4)
            if len(parts) < 5:
                continue

            owner, repo_name, _, branch, filepath = parts
            filename = filepath.split("/")[-1]

            results.append({
                "name": filename,
                "path": filepath,
                "repo": f"{owner}/{repo_name}",
                "owner": owner,
                "repo_name": repo_name,
                "branch": branch,
                "url": f"https://github.com{href}",
                "raw_url": f"https://raw.githubusercontent.com/{owner}/{repo_name}/{branch}/{filepath}",
            })

            if len(results) >= max_results:
                break

    except Exception:
        pass

    _polite_sleep()
    return results[:max_results]


# ── 3. Fetch File Content ─────────────────────────────────────────────

def fetch_github_file(owner, repo, filepath, branch=None):
    """
    Ambil isi file dari raw.githubusercontent.com.
    Auto-detect branch: coba main → master → scrape halaman repo.
    """
    branches_to_try = [branch] if branch else ["main", "master", "dev", "develop"]

    for br in branches_to_try:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{br}/{filepath}"
        resp = _safe_get(url, timeout=10)
        if resp and resp.ok and resp.text.strip():
            return resp.text
        _polite_sleep()

    return ""


def fetch_file_from_blob_url(blob_url):
    """
    Ambil isi file dari URL blob GitHub.
    Contoh: https://github.com/owner/repo/blob/main/file.py
    → Konversi ke raw URL.
    """
    raw_url = blob_url.replace(
        "https://github.com/", "https://raw.githubusercontent.com/"
    ).replace("/blob/", "/")
    resp = _safe_get(raw_url, timeout=10)
    if resp and resp.ok:
        return resp.text
    return ""


# ── 4. Trending Repos ─────────────────────────────────────────────────

def fetch_trending_repos(language="python", since="daily"):
    """
    Scrape halaman GitHub Trending.
    URL: https://github.com/trending/{language}?since={since}
    """
    repos = []
    try:
        url = f"https://github.com/trending/{language}?since={since}"
        resp = _safe_get(url)
        if not resp:
            return repos

        soup = BeautifulSoup(resp.text, "lxml")

        for article in soup.select("article.Box-row"):
            try:
                # Nama repo
                name_el = article.select_one("h2.h3 a, h2 a")
                if not name_el:
                    continue

                href = name_el.get("href", "").strip("/")
                parts = href.split("/")
                if len(parts) < 2:
                    continue

                owner, repo_name = parts[0], parts[1]
                full_name = f"{owner}/{repo_name}"

                # Deskripsi
                desc_el = article.select_one("p.col-9, p[class*='color-fg-muted']")
                description = desc_el.get_text(strip=True) if desc_el else ""

                # Total bintang
                stars_el = article.select_one(
                    "a[href$='/stargazers'], a.Link--muted svg[aria-label='star'] + span, "
                    "a[href*='stargazers']"
                )
                if stars_el:
                    stars = stars_el.parent.get_text(strip=True) if stars_el else "?"
                else:
                    # Cari semua a.Link--muted dan ambil yang pertama (biasanya stars)
                    muted = article.select("a.Link--muted")
                    stars = muted[0].get_text(strip=True) if muted else "?"

                # Bahasa
                lang_el = article.select_one(
                    "span[itemprop='programmingLanguage'], "
                    "span[data-testid='language']"
                )
                lang = lang_el.get_text(strip=True) if lang_el else language

                # Stars hari ini
                stars_today_el = article.select_one("span.d-inline-block.float-sm-right")
                stars_today = stars_today_el.get_text(strip=True) if stars_today_el else ""

                repos.append({
                    "name": full_name,
                    "description": description[:250],
                    "url": f"https://github.com/{full_name}",
                    "stars": stars,
                    "stars_today": stars_today,
                    "language": lang,
                    "owner": owner,
                    "repo": repo_name,
                })

                if len(repos) >= 20:
                    break
            except Exception:
                continue

    except Exception:
        pass

    _polite_sleep()
    return repos


# ── 5. Repo README & File List ────────────────────────────────────────

def fetch_repo_readme(owner, repo):
    """Ambil README dari repo. Coba berbagai nama file umum."""
    readme_names = ["README.md", "readme.md", "README.rst", "README.txt", "README"]
    for name in readme_names:
        content = fetch_github_file(owner, repo, name)
        if content:
            return content
        time.sleep(0.5)
    return ""


def fetch_repo_files(owner, repo, path="", branch=None):
    """
    Scrape daftar file dari halaman repo GitHub.
    Tanpa API — menjelajahi tampilan web biasa.
    """
    files = []
    branches_to_try = [branch] if branch else ["main", "master"]

    for br in branches_to_try:
        try:
            sub_path = f"/tree/{br}/{path}" if path else f"/tree/{br}"
            url = f"https://github.com/{owner}/{repo}{sub_path}"
            resp = _safe_get(url)
            if not resp:
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            # GitHub file table rows
            for row in soup.select("tr.react-directory-row, div[role='row']"):
                try:
                    link = row.select_one("a[href]")
                    if not link:
                        continue

                    href = link.get("href", "")
                    name = link.get_text(strip=True)

                    # Tentukan tipe: blob = file, tree = folder
                    ftype = "file" if "/blob/" in href else "dir" if "/tree/" in href else "file"

                    files.append({
                        "name": name,
                        "path": href.split(f"/{br}/", 1)[-1] if f"/{br}/" in href else name,
                        "type": ftype,
                        "url": f"https://github.com{href}",
                    })
                except Exception:
                    continue

            if files:
                break  # Berhasil, tidak perlu coba branch lain
        except Exception:
            continue
        finally:
            _polite_sleep()

    return files


# ── 6. Collect Code Snippets ──────────────────────────────────────────

def collect_code_snippets(query, language="python", max_total=10):
    """
    Kumpulkan code snippets dari GitHub search.
    Etis: jeda antar setiap request, max snippet terbatas.
    """
    snippets = []

    code_results = search_github_code(query, language, max_results=5)
    for result in code_results[:5]:
        if len(snippets) >= max_total:
            break

        raw_url = result.get("raw_url", "")
        if not raw_url:
            # Bangun raw URL dari info yang ada
            owner = result.get("owner", "")
            repo = result.get("repo_name", "")
            branch = result.get("branch", "main")
            path = result.get("path", "")
            if owner and repo and path:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"

        if raw_url:
            resp = _safe_get(raw_url, timeout=10)
            if resp and resp.ok and resp.text.strip():
                code = resp.text.strip()
                # Ambil maksimal 3000 karakter
                snippets.append(code[:3000])
            _polite_sleep()

    return snippets[:max_total]


# ── 7. Get Repo Info (scrape halaman repo) ────────────────────────────

def get_repo_info(owner, repo):
    """
    Scrape informasi lengkap sebuah repo dari halaman web-nya.
    """
    info = {
        "name": f"{owner}/{repo}",
        "url": f"https://github.com/{owner}/{repo}",
        "description": "",
        "stars": "",
        "forks": "",
        "language": "",
        "topics": [],
        "license": "",
        "readme_preview": "",
    }
    try:
        url = f"https://github.com/{owner}/{repo}"
        resp = _safe_get(url)
        if not resp:
            return info

        soup = BeautifulSoup(resp.text, "lxml")

        # Deskripsi
        desc = soup.select_one("p.f4.my-3, p[data-testid='repo-description']")
        if desc:
            info["description"] = desc.get_text(strip=True)[:300]

        # Stars
        star_el = soup.select_one(
            "a[href$='/stargazers'] span, #repo-stars-counter-star, "
            "span[id*='stargazers']"
        )
        if star_el:
            info["stars"] = star_el.get_text(strip=True)

        # Forks
        fork_el = soup.select_one(
            "a[href$='/forks'] span, #repo-network-counter, "
            "span[id*='forks']"
        )
        if fork_el:
            info["forks"] = fork_el.get_text(strip=True)

        # Bahasa utama
        lang_el = soup.select_one("span[itemprop='programmingLanguage']")
        if lang_el:
            info["language"] = lang_el.get_text(strip=True)

        # Topics
        for topic in soup.select("a.topic-tag")[:10]:
            info["topics"].append(topic.get_text(strip=True))

        # Lisensi
        license_el = soup.select_one("a[href$='/blob/main/LICENSE'], a[href*='/blob/'][href*='license']")
        if license_el:
            info["license"] = license_el.get_text(strip=True)

    except Exception:
        pass

    _polite_sleep()
    return info
