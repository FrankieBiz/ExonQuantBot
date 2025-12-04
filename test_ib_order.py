from ib_insync import *
import time

# Connect to TWS or IB Gateway paper trading instance
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # default for TWS paper

# Define stock contract
contract = Stock('AAPL', 'SMART', 'USD')

# Request market data (optional, to check connection)
ticker = ib.reqMktData(contract)
time.sleep(1)

print(f'Latest AAPL price: {ticker.marketPrice()}')

# Place a dummy buy limit order for 1 share well below market (it probably won't fill)
order = LimitOrder('BUY', 1, ticker.marketPrice()-10)
trade = ib.placeOrder(contract, order)
print('Order placed!')

# Wait 5 seconds, then disconnect
time.sleep(5)
ib.disconnect()
