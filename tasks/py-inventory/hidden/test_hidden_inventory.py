import unittest
from decimal import Decimal

from inventory import Inventory, OutOfStock, order_total


def make():
    inv = Inventory()
    inv.add_item("A", Decimal("10.00"), 5)
    inv.add_item("B", Decimal("2.50"), 10)
    return inv


class HiddenInventory(unittest.TestCase):
    def test_discount_applied_once(self):
        self.assertEqual(order_total([(Decimal("10.00"), 2)], "SAVE10"), Decimal("19.44"))

    def test_half_discount_multi_line(self):
        self.assertEqual(order_total([(Decimal("10.00"), 1), (Decimal("2.50"), 4)], "HALF"), Decimal("10.80"))

    def test_unknown_code(self):
        with self.assertRaises(ValueError):
            order_total([(Decimal("1"), 1)], "NOPE")

    def test_order_exact_stock(self):
        inv = make()
        inv.order({"A": 5})
        self.assertEqual(inv.stock("A"), 0)

    def test_out_of_stock_all_or_nothing(self):
        inv = make()
        with self.assertRaises(OutOfStock):
            inv.order({"B": 3, "A": 6})
        self.assertEqual(inv.stock("B"), 10)
        self.assertEqual(inv.history, [])

    def test_order_total_with_code(self):
        inv = make()
        self.assertEqual(inv.order({"A": 2}, "SAVE10"), Decimal("19.44"))
        self.assertEqual(inv.history, [("order", {"A": 2}, "SAVE10")])

    def test_restock(self):
        inv = make()
        inv.restock("A", 3)
        self.assertEqual(inv.stock("A"), 8)
        self.assertEqual(inv.history[-1], ("restock", "A", 3))

    def test_restock_errors(self):
        inv = make()
        with self.assertRaises(KeyError):
            inv.restock("Z", 1)
        for bad in (0, -1, 1.5, "2"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    inv.restock("A", bad)


if __name__ == "__main__":
    unittest.main()
