import yfinance as yf

# Get the real-time price of a selected coin
def get_coin_price(coin):
    # Create a Ticker object for the selected coin
    ticker = yf.Ticker(f"{coin}-USD")
    # Get the latest price data for the selected coin
    data = ticker.history()
    return data['Close'].iloc[-1]

# Calculate the amount in the selected coin for the selected package
def calculate_amount(package_price, coin):
    # Get the real-time price of the selected coin
    coin_price = get_coin_price(coin)
    # Calculate the amount in the selected coin for the selected package
    amount = package_price / coin_price
    # Return the amount in the selected coin
    return round(amount, 4)