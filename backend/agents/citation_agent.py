"""Citation formatting in APA, IEEE, and MLA styles."""

import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def _get_author_list(source: dict[str, Any]) -> str:
    authors = source.get("authors", source.get("author", ""))
    if isinstance(authors, list):
        return ", ".join(authors)
    return str(authors) if authors else "Unknown Author"


def _get_year(source: dict[str, Any]) -> str:
    year = source.get("year", "")
    if not year:
        date_str = source.get("date", source.get("published", ""))
        if date_str:
            match = re.search(r"\d{4}", str(date_str))
            if match:
                return match.group()
    return str(year) if year else str(datetime.now().year)


def format_apa(source: dict[str, Any], index: int | None = None) -> str:
    authors = _get_author_list(source)
    year = _get_year(source)
    title = source.get("title", "Untitled")
    url = source.get("url", "")

    if source.get("type") == "web":
        return f"{authors}. ({year}). {title}. Retrieved from {url}"
    return f"{authors}. ({year}). {title}. {source.get('journal', source.get('publisher', ''))}. {url}".strip()


def format_ieee(source: dict[str, Any], index: int) -> str:
    authors = _get_author_list(source)
    title = source.get("title", "Untitled")
    url = source.get("url", "")
    year = _get_year(source)
    return f'[{index}] {authors}, "{title}," {year}. [Online]. Available: {url}'


def format_mla(source: dict[str, Any], index: int | None = None) -> str:
    authors = _get_author_list(source)
    title = source.get("title", "Untitled")
    url = source.get("url", "")
    site = source.get("site", source.get("domain", "Web"))
    year = _get_year(source)
    return f'{authors}. "{title}." {site}, {year}, {url}.'


def build_bibliography(sources: list[dict[str, Any]], style: str = "apa") -> list[str]:
    """Build formatted bibliography from retrieved sources only."""
    style = style.lower()
    bibliography: list[str] = []

    seen_urls: set[str] = set()
    unique_sources: list[dict[str, Any]] = []
    for src in sources:
        url = src.get("url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        unique_sources.append(src)

    for i, src in enumerate(unique_sources, 1):
        try:
            if style == "ieee":
                bibliography.append(format_ieee(src, i))
            elif style == "mla":
                bibliography.append(format_mla(src, i))
            else:
                bibliography.append(format_apa(src, i))
        except Exception:
            logger.warning("Failed to format citation for source: %s", src.get("title"))
            bibliography.append(f"[{i}] {src.get('title', 'Unknown')} — {src.get('url', '')}")

    return bibliography


def extract_citation_from_search_result(result: dict[str, Any]) -> dict[str, Any]:
    """Convert a search/scrape result into a citable source."""
    return {
        "title": result.get("title", "Untitled"),
        "url": result.get("url", result.get("href", "")),
        "authors": result.get("authors", result.get("author", "Unknown")),
        "snippet": result.get("snippet", result.get("body", "")),
        "type": result.get("source", "web"),
        "domain": result.get("domain", ""),
        "year": result.get("year", ""),
    }
