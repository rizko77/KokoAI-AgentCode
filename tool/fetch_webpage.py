import requests
from bs4 import BeautifulSoup
from config.settings import USER_AGENT, REQUEST_TIMEOUT


def fetch_url(url):
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)

        return {
            "status_code": response.status_code,
            "url": response.url,
            "content_type": response.headers.get("Content-Type", ""),
            "content_length": len(response.text),
            "text": response.text,
            "ok": response.ok,
        }

    except requests.Timeout:
        return {"error": "Request timeout", "ok": False}
    except requests.ConnectionError:
        return {"error": "Connection error - periksa koneksi internet", "ok": False}
    except Exception as e:
        return {"error": str(e), "ok": False}


def fetch_json(url):
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        return {"error": str(e)}


def fetch_page_title(url):
    try:
        result = fetch_url(url)
        if not result.get("ok"):
            return "N/A"

        soup = BeautifulSoup(result["text"], "lxml")
        title = soup.find("title")
        return title.get_text(strip=True) if title else "No Title"

    except Exception:
        return "N/A"


def fetch_github_raw(owner, repo, filepath, branch="main"):
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filepath}"
    result = fetch_url(url)

    if result.get("ok"):
        return result.get("text", "")
    return ""


def is_url_accessible(url):
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.head(url, headers=headers, timeout=5)
        return response.status_code < 400
    except Exception:
        return False
