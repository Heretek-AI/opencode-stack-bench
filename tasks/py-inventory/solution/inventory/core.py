from decimal import Decimal

from .pricing import order_total


class OutOfStock(Exception):
    pass


class Inventory:
    def __init__(self):
        self._items = {}
        self.history = []

    def add_item(self, sku: str, price: Decimal, stock: int):
        if sku in self._items:
            raise ValueError(f"duplicate sku: {sku}")
        self._items[sku] = {"price": Decimal(price), "stock": int(stock)}

    def stock(self, sku: str) -> int:
        return self._items[sku]["stock"]

    def order(self, items, code=None) -> Decimal:
        """items: dict sku -> qty. All-or-nothing: no stock changes if any line fails."""
        for sku, qty in items.items():
            if self._items[sku]["stock"] < qty:
                raise OutOfStock(sku)
        lines = []
        for sku, qty in items.items():
            self._items[sku]["stock"] -= qty
            lines.append((self._items[sku]["price"], qty))
        total = order_total(lines, code)
        self.history.append(("order", dict(items), code))
        return total

    def restock(self, sku: str, qty: int):
        if sku not in self._items:
            raise KeyError(sku)
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            raise ValueError(f"qty must be a positive integer: {qty!r}")
        self._items[sku]["stock"] += qty
        self.history.append(("restock", sku, qty))
