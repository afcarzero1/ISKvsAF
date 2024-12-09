import argparse

import pandas as pd

from investments.portfolio import Portfolio


def process_coinbase_csv(file_path):
    portfolio = Portfolio(base_currency='SEK')

    # Read the CSV using pandas and skip unnecessary rows
    df = pd.read_csv(file_path, skiprows=[0, 1])

    # Clean up the 'kr' prefix from relevant columns
    def clean_kr(value):
        if isinstance(value, str) and 'kr' in value:
            return float(value.replace('kr', '').replace(',', '').strip())
        return value

    # Apply cleanup to relevant columns
    for col in ['Price at Transaction', 'Subtotal', 'Total (inclusive of fees and/or spread)', 'Fees and/or Spread']:
        df[col] = df[col].apply(clean_kr)

    # Ensure the Timestamp column is in datetime format
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')

    # Sort the transactions by Timestamp
    df = df.sort_values(by='Timestamp')

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        # Extract necessary fields
        transaction_type = row['Transaction Type']
        timestamp = row['Timestamp']
        asset = row['Asset']
        quantity_transacted = row['Quantity Transacted']
        price_currency = row['Price Currency']  # Should be 'SEK'
        price_at_transaction = row['Price at Transaction']
        subtotal = row['Subtotal']
        total = row['Total (inclusive of fees and/or spread)']
        fees = row['Fees and/or Spread']
        notes = row['Notes']
        transaction_id = row['ID']

        # Skip transactions without quantity (e.g., deposits of fiat)
        if pd.isna(quantity_transacted) or quantity_transacted == '':
            continue

        quantity = float(quantity_transacted)
        price = float(price_at_transaction) if not pd.isna(price_at_transaction) else 0.0
        fee = float(fees) if not pd.isna(fees) else 0.0

        # Map transaction type to action
        if transaction_type in ['Buy', 'Advanced Trade Buy']:
            action = 'buy'
        elif transaction_type in ['Sell', 'Advanced Trade Sell']:
            action = 'sell'
        elif transaction_type == 'Deposit':
            action = 'deposit'
            # Check if the deposit is of an asset (crypto) or fiat
            if asset == 'SEK':
                # Deposit of fiat currency, we can skip or handle accordingly
                continue
            else:
                # Deposit of crypto asset
                price = 0.0  # No cost associated
                fee = 0.0
        elif transaction_type == 'Convert':
            action = 'convert'
            # Extract 'to_asset' from the 'Notes' field or another appropriate field
            # For example, Notes might be "Converted ETH to BTC"
            to_asset = extract_to_asset_from_notes(notes, asset)
            if not to_asset:
                print(f"Unable to determine 'to_asset' for conversion in transaction ID {transaction_id}. Skipping.")
                continue
        else:
            # Unknown transaction type
            print(f"Unknown transaction type '{transaction_type}' in transaction ID {transaction_id}. Skipping.")
            continue

        # Process the transaction
        try:
            portfolio.add_transaction(
                action=action,
                asset=asset,
                price=price,
                quantity=quantity,
                fee=fee,
                transaction_currency='SEK',
                timestamp=timestamp,
                to_asset=to_asset if action == 'convert' else None
            )
        except Exception as e:
            print(f"Error processing transaction ID {transaction_id}: {e}")
            continue

    # After processing all transactions, calculate total realized profit/loss
    total_profit_loss = portfolio.calculate_total_profit_loss()
    print(f"Total Realized Profit/Loss: {total_profit_loss:.2f} SEK")

    # Calculate tax
    if total_profit_loss > 0:
        tax = total_profit_loss * 0.30  # 30% tax on profits
        print(f"Total Tax to Pay: {tax:.2f} SEK")
    elif total_profit_loss < 0:
        deductible_loss = abs(total_profit_loss) * 0.70  # 70% of loss is deductible
        print(f"Total Deductible Loss: {deductible_loss:.2f} SEK")
    else:
        print("No profit or loss.")

    # Optionally, print detailed report
    print("\nDetailed Profit/Loss per Asset:")
    for asset, investment in portfolio.investments.items():
        total_pl = investment.total_realized_profit_loss()
        print(f"- {asset}: {total_pl:.2f} SEK")


def extract_to_asset_from_notes(notes, from_asset):
    """
    Extracts the 'to_asset' from the 'Notes' field in the Coinbase CSV.
    Example Notes: 'Converted BTC to ETH'
    """
    if pd.isna(notes) or not notes:
        return None
    # Example note: 'Converted BTC to ETH'
    parts = notes.split(' ')
    if 'to' in parts:
        to_index = parts.index('to')
        if to_index + 1 < len(parts):
            to_asset = parts[to_index + 1]
            if to_asset != from_asset:
                return to_asset
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process Coinbase CSV file to calculate tax.')
    parser.add_argument('file_path', type=str, help='Path to the Coinbase CSV file')

    args = parser.parse_args()
    process_coinbase_csv(args.file_path)
