from .investment import Investment


class Portfolio:
    def __init__(self, base_currency="SEK"):
        self.investments = {}  # Key: Asset name, Value: Investment instance
        self.base_currency = base_currency
        self.transactions = []  # Record of all transactions

    def add_transaction(
        self,
        action: str,
        asset: str,
        price: float,
        quantity: float,
        fee: float = 0,
        transaction_currency="SEK",
        timestamp=None,
        to_asset=None,
    ):
        # Since Coinbase data is already in SEK, we don't need to convert currencies
        price_in_base = price
        fee_in_base = fee

        # Get or create the Investment instance for the asset
        investment = self.investments.get(asset)
        if not investment:
            investment = Investment()
            self.investments[asset] = investment

        if action == "buy":
            investment.buy(price_in_base, quantity, fee_in_base)
        elif action == "sell":
            profit_loss = investment.sell(price_in_base, quantity, fee_in_base)
        elif action == "deposit":
            # For deposits of crypto assets, we can treat it as a buy with zero cost
            investment.buy(price=0, quantity=quantity, fee=0)
        elif action == "convert":
            if not to_asset:
                raise ValueError("Conversion requires a 'to_asset' parameter.")
            self.handle_conversion(
                asset, to_asset, quantity, price_in_base, fee_in_base, timestamp
            )
        else:
            raise ValueError(
                "Invalid action. Must be 'buy', 'sell', 'convert', or 'deposit'."
            )

        # Record the transaction
        self.transactions.append(
            {
                "timestamp": timestamp,
                "action": action,
                "asset": asset,
                "to_asset": to_asset,
                "price": price_in_base,
                "quantity": quantity,
                "fee": fee_in_base,
                "transaction_currency": transaction_currency,
            }
        )

    def handle_conversion(
        self,
        from_asset: str,
        to_asset: str,
        quantity: float,
        price_in_base: float,
        fee_in_base: float,
        timestamp,
    ):
        """
        Handles the conversion between two assets by treating it as a sell of 'from_asset' and a buy of 'to_asset'.
        """
        # Sell 'from_asset'
        from_investment = self.investments.get(from_asset)
        if not from_investment:
            raise ValueError(f"No holdings for asset {from_asset} to convert from.")

        # Calculate the quantity of 'from_asset' needed to get the desired quantity of 'to_asset'
        total_cost = (
            price_in_base * quantity + fee_in_base
        )  # Total cost in SEK to buy 'quantity' of 'to_asset'
        quantity_to_sell = (
            total_cost / from_investment.avg_price
        )  # Quantity of 'from_asset' to sell

        # Ensure we have enough of 'from_asset' to sell
        if quantity_to_sell > from_investment.quantity:
            raise ValueError(f"Not enough {from_asset} to complete the conversion.")

        # Sell 'from_asset'
        profit_loss_sell = from_investment.sell(
            from_investment.avg_price, quantity_to_sell, fee_in_base
        )

        # Buy 'to_asset'
        to_investment = self.investments.get(to_asset)
        if not to_investment:
            to_investment = Investment()
            self.investments[to_asset] = to_investment

        to_investment.buy(
            price_in_base, quantity, 0
        )  # Assume fee is applied on the sell side

        # Record the realized profit/loss from the sell side
        self.transactions.append(
            {
                "timestamp": timestamp,
                "action": "sell",
                "asset": from_asset,
                "price": from_investment.avg_price,
                "quantity": quantity_to_sell,
                "fee": fee_in_base,
                "transaction_currency": self.base_currency,
            }
        )

        # Record the buy transaction for 'to_asset'
        self.transactions.append(
            {
                "timestamp": timestamp,
                "action": "buy",
                "asset": to_asset,
                "price": price_in_base,
                "quantity": quantity,
                "fee": 0,
                "transaction_currency": self.base_currency,
            }
        )

    def get_investment(self, asset: str):
        return self.investments.get(asset)

    def calculate_total_profit_loss(self):
        total = 0
        for investment in self.investments.values():
            total += investment.total_realized_profit_loss()
        return total
