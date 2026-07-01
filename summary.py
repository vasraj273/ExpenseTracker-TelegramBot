"""Build the daily summary as a phone-friendly monospace table."""


def fmt_money(amount):
    """₹120 for whole numbers, ₹120.50 otherwise."""
    if float(amount).is_integer():
        return f"₹{int(amount)}"
    return f"₹{amount:.2f}"


def build_daily_summary(expenses, day_label):
    if not expenses:
        return f"🧾 {day_label}\nNo expenses logged today — ₹0 spent."

    header = ("Item", "Amount", "Category")
    rows = [header] + [
        (e["item"], fmt_money(e["amount"]), e["category"]) for e in expenses
    ]

    w_item = max(len(r[0]) for r in rows)
    w_amt = max(len(r[1]) for r in rows)
    w_cat = max(len(r[2]) for r in rows)

    def line(r):
        return f"{r[0]:<{w_item}}  {r[1]:>{w_amt}}  {r[2]:<{w_cat}}"

    table = [line(header), "-" * (w_item + w_amt + w_cat + 4)]
    table += [line(r) for r in rows[1:]]

    # per-category totals
    by_cat = {}
    for e in expenses:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]
    total = sum(e["amount"] for e in expenses)

    parts = [f"🧾 Expenses for {day_label}", "", "```", *table, "```", "", "By category:"]
    for cat, amt in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        parts.append(f"• {cat}: {fmt_money(amt)}")
    parts += ["", f"Total: {fmt_money(total)}"]

    return "\n".join(parts)
