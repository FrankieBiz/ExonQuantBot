from ib_insync import *
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)
print("Connected!" if ib.isConnected() else "Not connected.")
ib.disconnect()