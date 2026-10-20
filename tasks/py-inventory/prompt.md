Customers report that order totals in the `inventory` package are too low when a discount code is used,
and that ordering exactly the remaining stock fails. Find and fix the bugs.

Then add a `restock(sku, qty)` method to `Inventory` that increases stock for an existing SKU
(raise `KeyError` for an unknown SKU, `ValueError` if `qty` is not a positive integer) and records a
`("restock", sku, qty)` entry in `Inventory.history`, the same way orders are recorded.

Keep the existing public API working. There are some existing tests in `tests/`.
