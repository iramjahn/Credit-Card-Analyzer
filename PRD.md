# CardOptimizer — Product Requirements Document

**Author:** Ian Ramjahn · **Status:** MVP shipped · **Last updated:** July 2026

---

## Problem

US consumers hold 3–4 credit cards on average but leave rewards value on the
table because optimizing is tedious: every card has different bonus categories,
spend caps, portal-only rates, and annual fees. The mental math of "which card
do I swipe for this?" and "is this $250 annual fee actually paying for itself?"
is real work that most people simply don't do.

## Target user

**The casual optimizer**: holds 2–5 mainstream rewards cards, cares about
getting value from them, but won't maintain a spreadsheet. Not the churner
(who needs signup-bonus tracking across 20 cards) and not the cash-back-only
minimalist (who owns one card on purpose).

## Jobs to be done

1. *"Which of my cards should I use for this purchase?"*
2. *"Given how I actually spend, which card is worth adding — and is its fee justified?"*
3. *"Track my spending automatically so I don't have to type it in."*

## What we built (MVP scope)

| Feature | Why it made the cut |
|---|---|
| Per-purchase recommendation (top-5 ranked by cash value, with caveats for top-category cards) | The core JTBD; must be trustworthy |
| Cap-aware annual value / ROI calculator | Answers "is the fee worth it" — the #2 job |
| Spending-based card recommendation (ML) | Personalizes job #2 from transaction history |
| Transaction tracking + auth | Foundation for personalization |
| **Card ingestion agent** (scrape → extract → human review → publish) | Card data entry was the ops bottleneck; automation with a review gate scales the catalog without risking data quality |
| Custom cards | Long-tail cards we'll never cover centrally |

## What we explicitly cut (and why)

- **Real Plaid integration** — mocked behind the same API contract. The demo
  proves the UX; bank linking adds compliance scope that doesn't de-risk the
  core value prop. Ship gate for beta, not for MVP.
- **Signup-bonus modeling** — first-year value is SUB-dominated, but modeling
  it well requires spend-timeline simulation. Deferred; noted as a known
  accuracy limitation.
- **Rotating-category tracking** (Discover it, Freedom Flex quarters) —
  resolved conservatively to the base rate rather than guessing quarters.
  Honest under-promise beats wrong over-promise in a trust product.
- **Auto-publishing scraped cards** — extraction is ~90-95% accurate; a wrong
  reward rate in a financial recommendation destroys trust. Every ingested
  card passes a human review queue with field-level diffs.

## Key decisions & evidence

**1. Accuracy audit of the rewards engine.** An internal audit found two
structural biases: top-category cards (Citi Custom Cash) could *never* win a
recommendation (dead reward key), and Chase portal rates were applied to all
travel (overstating CSP by up to 2.5× on flights). Both fixed; spend caps
(Amex BCP $6k grocery cap, Citi $500/mo) added to the value model. The engine
is now covered by unit tests.

**2. Evaluated the ML recommender instead of assuming it works.** On 300
held-out synthetic users (cap-aware value model, $3k/month spend):

| Strategy | Oracle match | Mean regret ($/yr) |
|---|---|---|
| Direct vector scoring (oracle) | 100% | $0 |
| KMeans cluster-center scoring (current) | 77.7% | $13 |
| One-size-fits-all best card | 42.3% | $175 |

Takeaways: **personalization is worth ~$162/user/year** over recommending one
card to everyone — the product premise holds. But the KMeans indirection
*loses* $13/user/year vs simply scoring the user's own spending vector, and
never recommends edge-of-cluster cards (Freedom Unlimited: 0 cluster picks vs
25 oracle wins). **Decision: move recommendation to direct scoring; keep
clustering only for segment labels** ("You're a Frequent Traveler") and
cold-start smoothing (<5 transactions).

**3. $0-default ingestion agent.** The extraction engine is pluggable:
a free rule-based extractor is the default; LLM extraction (Claude, ~$0.05/card
at scale, structured-output JSON) is a config-flag upgrade when catalog breadth
justifies spend. Unit economics priced before building.

## Success metrics

- **Recommendation quality:** ≥95% oracle-match on the held-out eval
  (achievable by shipping direct scoring); $0 mean regret target.
- **Catalog:** 50 cards live with <10 min human review time per card via the
  ingest queue.
- **Engagement (post-beta):** % of users with ≥1 linked account; weekly
  recommendation queries per active user.
- **Trust:** zero published cards with incorrect fee/rate data (review-gate SLA).

## Risks

- **Data licensing:** scraping issuer sites violates most ToS. Portfolio-scale
  is low-stakes; production requires licensed data or issuer partnerships.
- **Accuracy liability:** value estimates are models, not guarantees; UI must
  present caveats (already returned via recommendation `note` field).
- **Plaid scope:** bank credentials raise the security bar (secrets management,
  token storage) beyond current dev-grade auth defaults.

## Roadmap

1. **Now:** ship direct-scoring recommendations (eval-backed), seed catalog to
   50 cards via ingest queue.
2. **Beta:** real Plaid sandbox integration; benefit-usage tracking (engine
   already built); signup-bonus first-year modeling.
3. **Later:** rotating-quarter calendar, multi-card wallet optimization
   ("your 3 cards cover 92% of optimal — here's the one card to add").
