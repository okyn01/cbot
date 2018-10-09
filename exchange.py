from binance.client import Client
import json
import helper as hlp

class Exchange:
	"""Handles all exchange functions for binance"""

	def __init__(self):
		"""Initialize the exchange class and connect to binance using api key and secret"""
		data = json.load(open('binance_auth.json'))
		api = {
			'key': data['key'],
			'secret': data['secret'],
			}

		self.client = Client(api['key'], api['secret'])

	def getAllSymbols(self, quoteAsset='USDT'):
		"""
			Get all symbols from binance using an asset, default is USDT.
			Possible to exclude certain base assets such as TUSD
			tickSize is used to define price interval
			stepSize is used to define amount interval
		"""
		exinfo = self.client.get_exchange_info()
		symbolList = []
		for symbol in exinfo['symbols']:
			if symbol['baseAsset'] != 'TUSD': # EXCLUDE
				if(symbol['quoteAsset'] == quoteAsset and symbol['status'] == 'TRADING'):
					symbolList.append({
						'symbol': symbol['symbol'],
						'quoteAsset': symbol['quoteAsset'],
						'baseAsset': symbol['baseAsset'],
						'minPrice': symbol['filters'][0]['minPrice'],
						'tickSize': symbol['filters'][0]['tickSize'],
						'stepSize': symbol['filters'][1]['stepSize']
					})

		return symbolList

	def getCurrentPrice(self, symbol):
		"""Get the current price of a symbol"""
		price = self.client.get_symbol_ticker(symbol=symbol)
		return float(price['price'])

	def getBidPrice(self, symbol):
		"""Get the current bid price of a symbol (someone is buying for)"""
		depth = self.client.get_order_book(symbol=symbol) 
		return float(depth['bids'][0][0])

	def getAskPrice(self, symbol):
		"""Get the current ask price of a symbol (someone is selling for)"""
		depth = self.client.get_order_book(symbol=symbol) 
		return float(depth['asks'][0][0])

	def getVolume(self, symbol):
		"""Get the volume of a symbol"""
		info = self.client.get_ticker(symbol=symbol)
		volume = info['quoteVolume']
		return float(volume)

	def getBalance(self, asset):
		"""Get available balance of asset"""
		balance = self.client.get_asset_balance(asset, recvWindow=10000)
		return float(balance['free'])

	def getTotalBalance(self, asset):
		"""Get available balance of asset and balance that is in open orders"""
		balance = self.client.get_asset_balance(asset, recvWindow=10000)
		return float(balance['free']) + float(balance['locked'])

	def buyLimit(self, symbol, amount, price):
		"""Create a limit buy order and return order ID"""
		print(symbol, amount, price)
		order = self.client.order_limit_buy(symbol=symbol, quantity=amount,	price=price, recvWindow=10000)
		return order

	def sellLimit(self, symbol, amount, price):
		"""Create a limit sell order and return order ID"""
		order = self.client.order_limit_sell(symbol=symbol, quantity=amount, price=price, recvWindow=10000)
		return order

	def buyMarket(self, symbol, amount):
		"""Buy asset for current market price and return order ID"""
		order = self.client.order_market_buy(symbol=symbol,	quantity=amount, recvWindow=10000)
		return order

	def sellMarket(self, symbol, amount):
		"""Sell asset for current market price and return order ID"""
		order = self.client.order_market_sell(symbol=symbol, quantity=amount, recvWindow=10000)
		return order

	def checkOrder(self, symbol, orderId):
		"""Get an order status"""
		order = self.client.get_order(symbol=symbol, orderId=orderId, recvWindow=10000)
		return order

	def cancelOrder(self, symbol, orderId):
		"""Cancel an order"""
		order = self.client.cancel_order(symbol=symbol, orderId=orderId, recvWindow=10000)
		return order

	def openOrderCount(self):
		"""Returns the amount of current open orders"""
		orderCount = self.client.get_open_orders(recvWindow=10000)
		return len(orderCount)

	def symbolExistsOrders(self, orders, symbol):
		"""Returns true if an order with given symbol already exists"""
		orders = self.client.get_open_orders(recvWindow=10000)
		for order in orders:
			if symbol == order['symbol']:
				return True
		return False

	def getSpread(self, symbol):
		spread = hlp.diff(self.getBidPrice(symbol), self.getAskPrice(symbol))
		return float(spread)
