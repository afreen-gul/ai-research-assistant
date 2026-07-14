"""Web page scraping and content extraction."""

import logging
import re
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (compatible; AIResearchAssistant/1.0; +https://github.com/research-assistant)"
)


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def scrape_url(url: str, max_chars: int = 15000) -> dict[str, Any]:
    """Fetch and extract main content from a URL."""
    logger.info("Scraping URL: %s", url)
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            html = response.text
    except Exception:
        logger.exception("Failed to fetch URL: %s", url)
        raise

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
        tag.decompose()

    title = ""
    if soup.title:
        title = _clean_text(soup.title.get_text())
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"]

    main_content = soup.find("article") or soup.find("main") or soup.find("body")
    text = _clean_text(main_content.get_text(separator="\n")) if main_content else ""

    if len(text) > max_chars:
        text = text[:max_chars] + "..."

    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""

    return {
        "url": url,
        "title": title,
        "description": description,
        "text": text,
        "domain": parsed.netloc,
        "char_count": len(text),
    }


def summarize_url_content(content: dict[str, Any]) -> str:
    """Format scraped content for LLM consumption."""
    return (
        f"Title: {content.get('title', 'Unknown')}\n"
        f"URL: {content.get('url', '')}\n"
        f"Description: {content.get('description', '')}\n\n"
        f"Content:\n{content.get('text', '')}"
    )
