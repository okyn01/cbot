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

		self.stopLossPrice = hlp.roundPrice(float(self.order['buyPrice']) * (1 - (float(self.cfg['stopLossPercentage']) / 100)), self.order['tickSize'])
		self.minSellPrice = hlp.roundPrice(float(self.order['buyPrice']) * (1 + (float(self.cfg['trailThreshold']) / 100)), self.order['tickSize'])
		self.maxSellPrice = hlp.roundPrice(float(self.order['buyPrice']) * (1 + (float(self.cfg['maxProfitPercentage']) / 100)), self.order['tickSize'])
		self.trailDeviation = 1 - (float(self.cfg['trailDeviation']) / 100)

		Exchange.__init__(self)
		Thread.__init__(self)
		self.daemon = True
		self.start()

	def run(self):
		sellingState = True
		highestPrice = float(self.order['buyPrice'])

		self.order['sellID'] = self.sellLimit(self.order['symbol'], self.order['amount'], self.maxSellPrice)
		while sellingState:
			currentPrice = float(self.getBidPrice(self.order['symbol']))

			priceDifference = hlp.diff(self.order['buyPrice'], currentPrice)

			print(self.order['symbol'], 
					'- Buy price:', self.order['buyPrice'], 
					'- Current price:', currentPrice, 
					'- Min profit price:', self.minSellPrice,
					'- Difference:', priceDifference)

			if(currentPrice > float(highestPrice)):
				highestPrice = currentPrice

			if((highestPrice * self.trailDeviation) <= currentPrice and float(self.minSellPrice) <= currentPrice):
				# SELL WITH PROFIT YAY :) 
				self.cancelOrder(self.order['symbol'], self.order['sellID'])
				#self.order['sellPrice'] = hlp.formatFloat(currentPrice)
				#self.order['sellID'] = self.sellLimit(self.order['symbol'], self.order['amount'], self.order['sellPrice'])
				self.order['sellID'] = self.sellMarket(self.order['symbol'], self.order['amount'])
				sellingState = False
				self.checkSellOrder(self.order['sellID'])

			if(currentPrice <= float(self.stopLossPrice)):
				# CANCEL MAX PROFIT ORDER AND THEN SELL FOR STOP LOSS [RIP MONEY] :(
				self.cancelOrder(self.order['symbol'], self.order['sellID'])
				self.order['sellID'] = self.sellMarket(self.order['symbol'], self.order['amount'])
				sellingState = False
				self.checkSellOrder(self.order['sellID'])

			time.sleep(2)


	def checkSellOrder(self, order):
		sellOrderState = True
		while sellOrderState:
			order = self.checkOrder(self.order['symbol'], self.order['sellID'])
			if(order['status'] == "FILLED"):
				sellOrderState = False
				priceDifference = hlp.diff(self.order['buyPrice'], order['price'])
				print('[SOLD] Order ID:', self.order['orderID'], '- Ticker:', self.order['symbol'], '- Difference:', priceDifference)
			time.sleep(10)
		return
