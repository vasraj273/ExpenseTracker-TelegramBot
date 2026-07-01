"""Parse a free-form chat message into an expense.

Rules (see PROJECT.md):
  * Free word order, no punctuation required.
  * Amount   = the numeric token (₹ optional, commas + decimals allowed).
  * Category = the token matching one of the user's registered categories.
  * Item     = everything left over (can be multi-word).
"""

import re
from dataclasses import dataclass, field

# Matches: 120  ₹120  120.50  ₹1,200.50  1,00,000
_AMOUNT_RE = re.compile(r"^₹?\s*(\d[\d,]*(?:\.\d+)?)$")


@dataclass
class ParseResult:
    status: str                       # "ok" | "no_amount" | "unknown_category"
    item: str = ""
    amount: float = 0.0
    category: str = ""
    unknown_tokens: list = field(default_factory=list)


def _parse_amount(token):
    m = _AMOUNT_RE.match(token)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def parse_message(text, known_categories):
    tokens = (text or "").split()
    if not tokens:
        return ParseResult(status="no_amount")

    known = {c.lower() for c in known_categories}

    # 1) find the amount (first numeric token)
    amount = None
    amount_idx = None
    for i, tok in enumerate(tokens):
        val = _parse_amount(tok)
        if val is not None:
            amount, amount_idx = val, i
            break

    if amount is None:
        return ParseResult(status="no_amount")

    rest = [t for i, t in enumerate(tokens) if i != amount_idx]

    # 2) find the category (first token matching a registered category)
    category = None
    cat_idx = None
    for i, tok in enumerate(rest):
        if tok.lower() in known:
            category, cat_idx = tok.lower(), i
            break

    if category is None:
        return ParseResult(
            status="unknown_category",
            amount=amount,
            unknown_tokens=rest,
        )

    # 3) whatever remains is the item (multi-word ok)
    item = " ".join(t for i, t in enumerate(rest) if i != cat_idx).strip()
    if not item:
        item = category  # e.g. "200 food" -> item defaults to the category word

    return ParseResult(status="ok", item=item, amount=amount, category=category)
