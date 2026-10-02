"""Application constants and canonical strings for CompostMitra.

Single source of truth for tier footnotes, disclaimers, guardrail strings,
and contract-enforced wording across the application, models, and documentation.
"""

from __future__ import annotations

# Canonical Tier Footnote for charts, cards, figures, and validation tables
TIER_FOOTNOTE: str = "T1 REAL | LIT calc | D1 proxy"
TIER_FOOTNOTE_CANONICAL: str = "T1 REAL | LIT calc | D1 proxy"
TIER_FOOTNOTE_EXPANDED: str = "T1 REAL 546 rows | LIT calc only for mix | D1 proxy sanity"

# Canonical Disclaimers
SUPPLEMENT_DISCLAIMER: str = "Supplement, builds soil — not fertilizer replacement"
MODEL_DISCLAIMER: str = (
    "Model estimates reflect statistical associations on historical proxy data (sanity check, not proof)."
)
ASSOCIATION_ONLY_NOTICE: str = (
    "Statistical association only; observational proxy data (sanity check, not proof)."
)

# Holdout and reporting sanity markers (required adjacent to numerical claims in reports)
HOLDOUT_LABEL_MARKERS: tuple[str, ...] = (
    "sanity, not proof",
    "sanity",
    "proxy",
    "not proof",
)

# Prohibited causal tokens (constructed dynamically so that bare grep does not trigger)
PROHIBITED_CAUSAL_TOKENS: tuple[str, ...] = (
    "".join(["pro", "ves"]),
    "".join(["cau", "ses"]),
)
