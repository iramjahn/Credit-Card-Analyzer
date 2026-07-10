# backend/integrations/card_ingest
#
# The card ingestion agent: fetch a card's web page, extract structured card
# data, validate it, and stage it for human review before it joins the live
# catalog. Runs at $0 by default (rule-based extractor); an LLM extractor can
# be enabled by setting ANTHROPIC_API_KEY.

from backend.integrations.card_ingest.pipeline import ingest_card_from_url

__all__ = ["ingest_card_from_url"]
