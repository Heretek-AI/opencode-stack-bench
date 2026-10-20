import unittest
from decimal import Decimal

from inventory import Inventory


class TestBasic(unittest.TestCase):
    def test_order_no_discount(self):
        inv = Inventory()
        inv.add_item("A", Decimal("10.00"), 5)
        self.assertEqual(inv.order({"A": 2}), Decimal("21.60"))
        self.assertEqual(inv.stock("A"), 3)


if __name__ == "__main__":
    unittest.main()
