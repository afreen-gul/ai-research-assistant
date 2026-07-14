"""Web search tool using DuckDuckGo via the `ddgs` package (no API key required)."""

import logging
import time
from typing import Any

from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException

logger = logging.getLogger(__name__)


def search_web(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    """Search the web and return structured results.

    Retries briefly on transient rate limits. Returns an empty list on failure
    so the agent can degrade gracefully instead of crashing.
    """
    logger.info("Web search: %s", query)
    results: list[dict[str, Any]] = []
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", r.get("link", r.get("url", ""))),
                        "snippet": r.get("body", r.get("snippet", "")),
                        "source": "web",
                    })
            break
        except RatelimitException:
            wait = attempt * 2
            logger.warning("DuckDuckGo rate-limited (attempt %d/%d), retrying in %ss", attempt, attempts, wait)
            if attempt < attempts:
                time.sleep(wait)
        except DDGSException:
            logger.exception("DuckDuckGo search failed for query: %s", query)
            break
        except Exception:
            logger.exception("Unexpected error during web search for query: %s", query)
            break

    logger.info("Search returned %d results", len(results))
    return results


def search_academic(query: str, max_results: int = 6) -> list[dict[str, Any]]:
    """Search for academic papers and repositories."""
    academic_query = f"{query} site:arxiv.org OR site:ieee.org OR site:acm.org OR site:github.com paper research"
    return search_web(academic_query, max_results=max_results)
