import unittest


class Investment:
    def __init__(self):
        self.quantity = 0
        self.total_cost = 0  # Total acquisition cost including fees
        self.realized_profit_loss = []  # Records of profits or losses from sales

    def buy(self, price: float, quantity: float, fee: float = 0):
        purchase_cost = price * quantity + fee
        self.total_cost += purchase_cost
        self.quantity += quantity

    def sell(self, price: float, quantity: float, fee: float = 0):
        if quantity > self.quantity:
            raise ValueError("Cannot sell more than the current quantity owned.")

        # Calculate sale proceeds and overhead amount using the average method
        sale_proceeds = price * quantity - fee
        overhead_amount = self.avg_price * quantity
        profit_loss = sale_proceeds - overhead_amount

        # Update total cost and quantity after the sale
        self.total_cost -= overhead_amount
        self.quantity -= quantity

        # Record the realized profit or loss
        self.realized_profit_loss.append(profit_loss)

        # Return the profit or loss for this transaction
        return profit_loss

    @property
    def avg_price(self):
        if self.quantity == 0:
            return 0
        return self.total_cost / self.quantity

    def total_realized_profit_loss(self):
        return sum(self.realized_profit_loss)


class TestInvestment(unittest.TestCase):
    def test_buy(self):
        inv = Investment()
        inv.buy(price=100, quantity=10, fee=5)
        self.assertEqual(inv.quantity, 10)
        self.assertEqual(inv.total_cost, 1005)
        self.assertAlmostEqual(inv.avg_price, 100.5)

    def test_multiple_buys(self):
        inv = Investment()
        inv.buy(price=100, quantity=10, fee=5)
        inv.buy(price=110, quantity=5, fee=2)
        self.assertEqual(inv.quantity, 15)
        self.assertEqual(inv.total_cost, 1557)
        self.assertAlmostEqual(inv.avg_price, 103.8)

    def test_sell(self):
        inv = Investment()
        inv.buy(price=100, quantity=10, fee=5)
        inv.buy(price=110, quantity=5, fee=2)
        profit_loss = inv.sell(price=120, quantity=8, fee=3)
        self.assertEqual(inv.quantity, 7)
        self.assertAlmostEqual(inv.total_cost, 726.6)
        self.assertAlmostEqual(inv.avg_price, 103.8)
        self.assertAlmostEqual(profit_loss, 126.6)
        self.assertEqual(len(inv.realized_profit_loss), 1)
        self.assertAlmostEqual(inv.total_realized_profit_loss(), 126.6)

    def test_sell_more_than_owned(self):
        inv = Investment()
        inv.buy(price=100, quantity=5)
        with self.assertRaises(ValueError):
            inv.sell(price=110, quantity=10)

    def test_complete_selling(self):
        inv = Investment()
        inv.buy(price=50, quantity=20)
        inv.sell(price=60, quantity=20)
        self.assertEqual(inv.quantity, 0)
        self.assertEqual(inv.total_cost, 0)
        self.assertEqual(inv.avg_price, 0)
        self.assertAlmostEqual(inv.total_realized_profit_loss(), 200)

    def test_loss_on_sale(self):
        inv = Investment()
        inv.buy(price=200, quantity=5, fee=10)
        profit_loss = inv.sell(price=190, quantity=5, fee=5)
        self.assertEqual(inv.quantity, 0)
        self.assertEqual(inv.total_cost, 0)
        self.assertAlmostEqual(profit_loss, -65)
        self.assertAlmostEqual(inv.total_realized_profit_loss(), -65)

    def test_avg_price_after_partial_sale(self):
        inv = Investment()
        inv.buy(price=100, quantity=10)
        inv.buy(price=150, quantity=10)
        inv.sell(price=130, quantity=5)
        self.assertEqual(inv.quantity, 15)
        self.assertAlmostEqual(inv.avg_price, 125)
        self.assertAlmostEqual(inv.total_cost, 1875)


if __name__ == "__main__":
    unittest.main()
