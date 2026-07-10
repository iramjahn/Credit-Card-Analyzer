# backend/integrations/card_ingest/fetcher.py
#
# Polite page fetcher for the ingest agent: respects robots.txt, rate-limits
# per domain, and identifies itself. Static HTML only (requests) — heavily
# JS-rendered issuer pages may return thin shells; those land in review as
# low-confidence candidates rather than failing silently.

import time
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger(__name__)

USER_AGENT = "CardOptimizerBot/1.0 (+card data ingestion; contact: admin@cardoptimizer.local)"
REQUEST_TIMEOUT = 15          # seconds
MIN_SECONDS_BETWEEN_HITS = 5  # per-domain rate limit

# domain -> unix timestamp of last fetch
_last_fetch: dict[str, float] = {}
# domain -> RobotFileParser (cached)
_robots_cache: dict[str, Optional[RobotFileParser]] = {}


def _robots_for(domain: str, scheme: str) -> Optional[RobotFileParser]:
    """Fetch and cache robots.txt for a domain. None means unavailable (allow)."""
    if domain in _robots_cache:
        return _robots_cache[domain]

    parser = RobotFileParser()
    parser.set_url(f"{scheme}://{domain}/robots.txt")
    try:
        parser.read()
        _robots_cache[domain] = parser
    except Exception:
        # robots.txt unreachable — treat as allowed but remember we tried
        _robots_cache[domain] = None
    return _robots_cache[domain]


def fetch_page(url: str) -> Tuple[bool, Optional[str], str]:
    """
    Fetch a URL politely.

    Returns (success, html, error_message).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, None, f"Unsupported URL scheme: {parsed.scheme!r}"
    domain = parsed.netloc

    robots = _robots_for(domain, parsed.scheme)
    if robots is not None and not robots.can_fetch(USER_AGENT, url):
        return False, None, f"robots.txt disallows fetching {url}"

    # Per-domain rate limit
    elapsed = time.monotonic() - _last_fetch.get(domain, 0.0)
    if elapsed < MIN_SECONDS_BETWEEN_HITS:
        time.sleep(MIN_SECONDS_BETWEEN_HITS - elapsed)

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        _last_fetch[domain] = time.monotonic()
        response.raise_for_status()
        return True, response.text, ""
    except requests.RequestException as exc:
        _last_fetch[domain] = time.monotonic()
        logger.warning("Fetch failed for %s: %s", url, exc)
        return False, None, f"Failed to fetch page: {exc}"
