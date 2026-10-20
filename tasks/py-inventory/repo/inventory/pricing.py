from decimal import Decimal, ROUND_HALF_UP

DISCOUNTS = {"SAVE10": Decimal("0.10"), "HALF": Decimal("0.50")}
TAX_RATE = Decimal("0.08")


def apply_discount(amount: Decimal, code=None) -> Decimal:
    if not code:
        return amount
    rate = DISCOUNTS.get(code)
    if rate is None:
        raise ValueError(f"unknown discount code: {code}")
    return amount * (1 - rate)


def order_total(lines, code=None) -> Decimal:
    """lines: iterable of (unit_price: Decimal, qty: int). Discount applies before tax."""
    subtotal = sum((apply_discount(price, code) * qty for price, qty in lines), Decimal("0"))
    discounted = apply_discount(subtotal, code)
    total = discounted * (1 + TAX_RATE)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
