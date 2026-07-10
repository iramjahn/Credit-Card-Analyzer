# backend/integrations/card_ingest/extractors.py
#
# Extraction engines for the ingest pipeline. Two implementations:
#
#   RuleBasedExtractor  — free, no API, the default. BeautifulSoup + pattern
#                         matching. Good enough to stage a candidate for human
#                         review; the reviewer fixes what it misses.
#   ClaudeExtractor     — optional LLM extraction (far more robust to page
#                         layout). Activates only when ANTHROPIC_API_KEY is
#                         set AND the `anthropic` package is installed, so the
#                         default deployment costs $0.
#
# Both return the same payload dict shape consumed by pipeline.py.

import os
import re
import logging
from typing import Dict, Optional, Tuple

from bs4 import BeautifulSoup

from backend.core.categories import SPENDING_CATEGORY_SET

logger = logging.getLogger(__name__)

# Categories the rule-based extractor knows how to spot in marketing copy,
# mapped to our canonical vocabulary. Non-canonical finds (e.g. "gas") are
# reported in `unmapped_rewards` for the human reviewer instead of silently
# polluting the rewards dict.
_REWARD_PATTERNS: Dict[str, list] = {
    "dining": [
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*|cash\s*back\s*)?(?:per\s*dollar\s*)?(?:on\s*)?dining",
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*|cash\s*back\s*)?at\s*restaurants",
    ],
    "travel": [
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*|cash\s*back\s*)?(?:per\s*dollar\s*)?on\s*travel",
    ],
    "flights": [
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*)?on\s*flights?",
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*)?on\s*airfare",
    ],
    "hotels": [
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*)?on\s*hotels?",
    ],
    "groceries": [
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*|cash\s*back\s*)?(?:per\s*dollar\s*)?(?:at\s*)?(?:U\.?S\.?\s*)?supermarkets?",
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*|cash\s*back\s*)?on\s*groceries",
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*)?at\s*grocery\s*stores",
    ],
    "streaming": [
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*|cash\s*back\s*)?on\s*(?:select\s*)?streaming",
    ],
    "transit": [
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*|cash\s*back\s*)?on\s*transit",
    ],
    "drugstores": [
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*|cash\s*back\s*)?at\s*drugstores?",
    ],
}

# Spotted but not in our canonical vocabulary — surfaced to the reviewer.
_NON_CANONICAL_PATTERNS: Dict[str, list] = {
    "gas": [
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*|cash\s*back\s*)?at\s*gas\s*stations?",
        r"(\d+(?:\.\d+)?)[x%]?\s*(?:points?\s*|cash\s*back\s*)?on\s*gas",
    ],
}

_ISSUER_DOMAINS = {
    "chase.com": "Chase",
    "americanexpress.com": "American Express",
    "amex": "American Express",
    "capitalone.com": "Capital One",
    "citi.com": "Citi",
    "discover.com": "Discover",
    "wellsfargo.com": "Wells Fargo",
    "bankofamerica.com": "Bank of America",
    "usbank.com": "U.S. Bank",
}

_BENEFIT_TEXT_PATTERNS = [
    r"no foreign transaction fees?",
    r"TSA PreCheck(?:/Global Entry)?(?:\s*credit)?",
    r"Global Entry(?:\s*credit)?",
    r"airport lounge access",
    r"priority boarding",
    r"free checked bags?",
    r"cell phone protection",
    r"rental car insurance",
    r"extended warranty",
    r"purchase protection",
    r"\$\d+\s*(?:annual\s*)?(?:travel|hotel|airline|uber|dining|statement|streaming)\s*credits?",
]


class RuleBasedExtractor:
    """Free extraction via HTML parsing + regex. No network, no API."""

    name = "rule-based"

    def extract(self, html: str, url: str) -> Tuple[bool, Optional[dict], str]:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        payload: dict = {
            "name": self._extract_name(soup),
            "issuer": self._extract_issuer(url),
            "annual_fee": self._extract_annual_fee(text),
            "point_value": 0.01,  # conservative default; reviewer can adjust
            "rewards": {"default": 1.0},
            "benefits": [],
            "signup_bonus": {},
            "unmapped_rewards": {},   # non-canonical categories, for the reviewer
            "confidence_notes": [],   # extraction caveats, for the reviewer
        }

        if not payload["name"]:
            return False, None, "Could not extract a card name from the page"

        # Rewards — canonical categories
        for category, patterns in _REWARD_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    payload["rewards"][category] = float(match.group(1))
                    break

        # Rewards — recognizable but non-canonical (flag, don't publish)
        for category, patterns in _NON_CANONICAL_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    payload["unmapped_rewards"][category] = float(match.group(1))
                    break

        # Base "everything" rate
        base = re.search(
            r"(\d+(?:\.\d+)?)\s*%\s*cash\s*back\s*on\s*(?:all|every)"
            r"|(\d+(?:\.\d+)?)[x]?\s*points?\s*on\s*(?:all|every)",
            text,
            re.IGNORECASE,
        )
        if base:
            payload["rewards"]["default"] = float(base.group(1) or base.group(2))

        # Annual fee sanity note
        if payload["annual_fee"] == 0 and "annual fee" not in text.lower():
            payload["confidence_notes"].append(
                "No annual-fee text found on page; defaulted to $0 — verify."
            )

        # Benefits
        for pattern in _BENEFIT_TEXT_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                benefit = match.group(0).strip()
                if benefit not in payload["benefits"]:
                    payload["benefits"].append(benefit)

        # Signup bonus (e.g. "earn 75,000 points after you spend $5,000")
        bonus = re.search(
            r"earn\s*([\d,]+)\s*(?:bonus\s*)?(?:points|miles)"
            r".{0,80}?spend(?:ing)?\s*\$([\d,]+)",
            text,
            re.IGNORECASE,
        )
        if bonus:
            payload["signup_bonus"] = {
                "amount": int(bonus.group(1).replace(",", "")),
                "spend_requirement": int(bonus.group(2).replace(",", "")),
            }

        if len(payload["rewards"]) == 1:
            payload["confidence_notes"].append(
                "Only a default reward rate was found — page may be JS-rendered "
                "or use uncommon phrasing. Review carefully."
            )

        return True, payload, ""

    def _extract_name(self, soup: BeautifulSoup) -> str:
        og_title = soup.find("meta", property="og:title")
        raw = ""
        if og_title and og_title.get("content"):
            raw = og_title["content"]
        else:
            title = soup.find("title")
            if title:
                raw = title.get_text()
        raw = raw.split("|")[0].strip()
        raw = re.sub(r"\s*Credit Card.*", "", raw, flags=re.IGNORECASE)
        return raw.strip()

    def _extract_issuer(self, url: str) -> str:
        lowered = url.lower()
        for domain, issuer in _ISSUER_DOMAINS.items():
            if domain in lowered:
                return issuer
        return "Unknown"

    def _extract_annual_fee(self, text: str) -> int:
        if re.search(r"(?:\$0|no)\s*(?:intro\s*)?annual fee", text, re.IGNORECASE):
            return 0
        for pattern in (
            r"\$(\d+)\s*annual fee",
            r"annual fee[:\s]*\$(\d+)",
            r"\$(\d+)\s*per year",
        ):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return 0


class ClaudeExtractor:
    """LLM extraction via the Claude API. Optional — costs money, so it only
    activates when ANTHROPIC_API_KEY is set and `anthropic` is installed."""

    name = "claude"

    @staticmethod
    def is_available() -> bool:
        if not os.getenv("ANTHROPIC_API_KEY"):
            return False
        try:
            import anthropic  # noqa: F401
            return True
        except ImportError:
            return False

    def extract(self, html: str, url: str) -> Tuple[bool, Optional[dict], str]:
        import anthropic
        from pydantic import BaseModel
        from typing import List as TList, Optional as TOptional

        class ExtractedCard(BaseModel):
            name: str
            issuer: str
            annual_fee: int
            rewards: Dict[str, float]           # category -> multiplier, incl. "default"
            benefits: TList[str]
            signup_bonus_amount: TOptional[int] = None
            signup_bonus_spend: TOptional[int] = None
            point_value_cents: TOptional[float] = None

        text = BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
        # Keep the request bounded — card terms live in the first chunk of copy.
        text = text[:60_000]

        client = anthropic.Anthropic()
        try:
            response = client.messages.parse(
                model="claude-opus-4-8",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": (
                        "Extract this credit card's terms from the page text below.\n"
                        f"Reward categories MUST be from this list: {sorted(SPENDING_CATEGORY_SET)} "
                        "plus 'default' for the base rate on everything else. "
                        "Express rates as multipliers (e.g. 3% cash back or 3x points -> 3.0). "
                        "If a value is not stated on the page, use a sensible conservative "
                        "default (annual_fee 0, point_value_cents 1.0) rather than guessing high.\n\n"
                        f"Source URL: {url}\n\nPage text:\n{text}"
                    ),
                }],
                output_format=ExtractedCard,
            )
        except anthropic.APIStatusError as exc:
            return False, None, f"Claude API error ({exc.status_code}): {exc.message}"
        except anthropic.APIConnectionError:
            return False, None, "Claude API unreachable"

        card = response.parsed_output
        if card is None:
            return False, None, "Claude returned no parseable card data"

        rewards = {k: float(v) for k, v in card.rewards.items()}
        rewards.setdefault("default", 1.0)
        payload = {
            "name": card.name,
            "issuer": card.issuer,
            "annual_fee": card.annual_fee,
            "point_value": (card.point_value_cents or 1.0) / 100.0,
            "rewards": rewards,
            "benefits": card.benefits,
            "signup_bonus": (
                {"amount": card.signup_bonus_amount, "spend_requirement": card.signup_bonus_spend}
                if card.signup_bonus_amount
                else {}
            ),
            "unmapped_rewards": {},
            "confidence_notes": [],
        }
        return True, payload, ""


def get_extractor():
    """Pick the best available extractor. Claude if configured, else free rule-based."""
    if ClaudeExtractor.is_available():
        logger.info("Using ClaudeExtractor (ANTHROPIC_API_KEY detected)")
        return ClaudeExtractor()
    return RuleBasedExtractor()
