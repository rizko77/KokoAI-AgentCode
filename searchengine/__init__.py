"""
KokoAI - Search Engine Module
Google Scraper, DuckDuckGo fallback, GitHub Code Search
"""
# Re-export dari tool.internet_search untuk backward compatibility
from tool.internet_search import (
    search_google,
    search_news,
    search_wikipedia,
    search_code,
    search_web,
    search_documentation,
)

__all__ = [
    "search_google",
    "search_news",
    "search_wikipedia",
    "search_code",
    "search_web",
    "search_documentation",
]
