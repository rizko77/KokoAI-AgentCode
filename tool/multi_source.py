import re
import time
import requests
from bs4 import BeautifulSoup
from config.settings import USER_AGENT, REQUEST_TIMEOUT


def scrape_stackoverflow(query, language="python", max_results=5):
    try:
        url = "https://api.stackexchange.com/2.3/search/advanced"
        params = {
            "order": "desc",
            "sort": "relevance",
            "q": query,
            "tagged": language,
            "site": "stackoverflow",
            "filter": "withbody",
            "pagesize": max_results,
        }
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "score": item.get("score", 0),
                "answers": item.get("answer_count", 0),
                "tags": item.get("tags", []),
                "is_answered": item.get("is_answered", False),
            })

        return results
    except Exception:
        return []


def scrape_stackoverflow_answers(question_id):
    try:
        url = f"https://api.stackexchange.com/2.3/questions/{question_id}/answers"
        params = {
            "order": "desc",
            "sort": "votes",
            "site": "stackoverflow",
            "filter": "withbody",
        }
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        code_snippets = []

        for answer in data.get("items", []):
            body = answer.get("body", "")
            soup = BeautifulSoup(body, "lxml")
            for code_block in soup.select("code, pre"):
                code = code_block.get_text(strip=True)
                if len(code) > 30:
                    code_snippets.append(code)

        return code_snippets
    except Exception:
        return []


def scrape_reddit_programming(query, subreddit="programming", max_results=5):
    try:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "on",
            "sort": "relevance",
            "limit": max_results,
        }
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        results = []

        children = data.get("data", {}).get("children", [])
        for child in children:
            post = child.get("data", {})
            results.append({
                "title": post.get("title", ""),
                "url": f"https://reddit.com{post.get('permalink', '')}",
                "score": post.get("score", 0),
                "comments": post.get("num_comments", 0),
                "selftext": post.get("selftext", "")[:500],
            })

        return results
    except Exception:
        return []


def scrape_gitlab_projects(query, language="python", max_results=5):
    try:
        url = "https://gitlab.com/api/v4/projects"
        params = {
            "search": query,
            "order_by": "stars",
            "sort": "desc",
            "per_page": max_results,
        }
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        results = []
        for project in response.json():
            results.append({
                "name": project.get("path_with_namespace", ""),
                "description": project.get("description", ""),
                "url": project.get("web_url", ""),
                "stars": project.get("star_count", 0),
            })
        return results
    except Exception:
        return []


def scrape_geeksforgeeks(query, language="python"):
    try:
        search_url = f"https://www.geeksforgeeks.org/search/{query}/"
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(search_url, headers=headers, timeout=REQUEST_TIMEOUT)

        if not response.ok:
            return []

        soup = BeautifulSoup(response.text, "lxml")
        results = []

        for article in soup.select("a.gc-card"):
            title = article.get_text(strip=True)
            href = article.get("href", "")
            if href and title:
                results.append({"title": title, "url": href})

            if len(results) >= 5:
                break

        return results
    except Exception:
        return []


def multi_source_search(query, language="python", sources=None):
    if sources is None:
        sources = ["stackoverflow", "github", "reddit"]

    all_results = {}

    if "stackoverflow" in sources:
        all_results["stackoverflow"] = scrape_stackoverflow(query, language)

    if "github" in sources:
        from tool.github_crawler import search_github_repos
        all_results["github"] = search_github_repos(query, language)

    if "reddit" in sources:
        subreddit = "learnpython" if language == "python" else "programming"
        all_results["reddit"] = scrape_reddit_programming(query, subreddit)

    if "gitlab" in sources:
        all_results["gitlab"] = scrape_gitlab_projects(query, language)

    return all_results


def collect_code_snippets(query, language="python", max_total=20):
    snippets = []

    so_results = scrape_stackoverflow(query, language, max_results=3)
    for result in so_results:
        url = result.get("url", "")
        match = re.search(r"/questions/(\d+)/", url)
        if match:
            qid = match.group(1)
            codes = scrape_stackoverflow_answers(qid)
            snippets.extend(codes[:3])

    from tool.github_crawler import search_github_code, fetch_github_file
    code_results = search_github_code(query, language, max_results=3)
    for result in code_results:
        repo = result.get("repo", "")
        path = result.get("path", "")
        if repo and path:
            parts = repo.split("/")
            if len(parts) == 2:
                code = fetch_github_file(parts[0], parts[1], path)
                if code and len(code) > 30:
                    snippets.append(code[:5000])

    return snippets[:max_total]
