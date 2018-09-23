from exchange import Exchange
from threading import Thread
import helper as hlp
import time
import json
import random

class Trailingstop(Thread, Exchange):
	def __init__(self, order):
		self.cfg = json.load(open('config.json'))
		self.order = order

		# Set statement for while loop till it's sold
		self.selling = True

		self.stopLossPrice = hlp.roundPrice(float(self.order['buyPrice']) * (1 - (float(self.cfg['stopLossPercentage']) / 100)), self.order['tickSize'])
		self.minProfitPrice = hlp.roundPrice(float(self.order['buyPrice']) * (1 + (float(self.cfg['minProfitPercentage']) / 100)), self.order['tickSize'])
		self.maxProfitPrice = hlp.roundPrice(float(self.order['buyPrice']) * (1 + (float(self.cfg['maxProfitPercentage']) / 100)), self.order['tickSize'])

		Exchange.__init__(self)
		Thread.__init__(self)
		self.daemon = True
		self.start()

	def run(self):
		highestPrice = self.order['buyPrice']

		self.order['sellID'] = self.sellLimit(self.order['symbol'], self.order['amount'], self.maxProfitPrice)
		while self.selling:
			currentPrice = float(self.getBidPrice(self.order['symbol']))

			priceDifference = hlp.diff(self.order['buyPrice'], currentPrice)

			print(self.order['symbol'], self.order['buyPrice'], currentPrice, priceDifference)

			if(currentPrice > float(highestPrice)):
				highestPrice = currentPrice
				print('Order ID:', self.order['orderID'], '- Ticker:', self.order['symbol'], '- Difference:', priceDifference)

			if(currentPrice >= float(self.minProfitPrice)):
				# currentprice is higher than min profit price 
				self.cancelOrder(self.order['symbol'], self.order['sellID'])
				self.sellLimit(self.order['symbol'], self.order['amount'], self.minProfitPrice)
				print('[SOLD] Order ID:', self.order['orderID'], '- Ticker:', self.order['symbol'], '- Difference:', priceDifference)

			if(currentPrice <= float(self.stopLossPrice)):
				# CANCEL MAX PROFIT ORDER AND THEN SELL FOR STOP LOSS
				self.cancelOrder(self.order['symbol'], self.order['sellID'])
				self.sellMarket(self.order['symbol'], self.order['amount'])
				print('[SOLD] Order ID:', self.order['orderID'], '- Ticker:', self.order['symbol'], '- Difference:', priceDifference)
				self.selling = False

			time.sleep(2)

		return
