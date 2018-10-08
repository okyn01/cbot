from trailingstop import Trailingstop
from exchange import Exchange
import winsound as ws
import helper as hlp
import time
import json
import strat

ex = Exchange()
cfg = json.load(open('config.json'))

pairs = ex.getAllSymbols('USDT')

orders = []

while True:
	for pair in pairs:

		orderCount = ex.openOrderCount()
		localTime = time.time()

		# SET BALANCE ACCORDING TO MAX ALLOWED ORDERS	
		balance = ex.getBalance(pair['quoteAsset'])
		if((int(cfg['maxOrders']) - orderCount) > 0):
			balance = balance / (int(cfg['maxOrders']) - orderCount)

		# MINIMUM BALANCE REQUIRED TO MAKE AN ORDER
		if(pair['quoteAsset'] == 'USDT'):
			minOrderValue = float(cfg['minOrderValueUSDT'])
		if(pair['quoteAsset'] == 'BTC'):
			minOrderValue = float(cfg['minOrderValueBTC'])

		print('Checking:', pair['symbol'])

		# STRATEGY
		df = strat.smoothHA(pair['symbol'], cfg['interval'], cfg['limit'], 10, 10)

		dfopen = float(df['HA_OpenEMA'].iloc[-1])
		dfclose = float(df['HA_CloseEMA'].iloc[-1])
		dfopenprev = float(df['HA_OpenEMA'].iloc[-2])
		dfcloseprev = float(df['HA_CloseEMA'].iloc[-2])

		dfhigh = float(df['High'].iloc[-1])
		dfhighprev = float(df['High'].iloc[-2])
		dfhighEMA = float(df['HA_HighEMA'].iloc[-1])
		dfhighprevEMA = float(df['HA_HighEMA'].iloc[-2])

		if(orderCount < int(cfg['maxOrders']) and ex.getVolume(pair['symbol']) > int(cfg['minVolume']) and balance > minOrderValue):
			# SET BUYPRICE, SELLPRICE AND AMOUNT TO BUY
			buyPrice = hlp.roundPrice(ex.getBidPrice(pair['symbol'])*0.99825, pair['tickSize'])
			amount = hlp.roundAmount(buyPrice, balance, pair['stepSize'])

			# EXECUTE STRAT
			#if(dfopen <= dfclose and dfopenprev >= dfcloseprev):
			if(dfhigh >= dfhighEMA and dfhighprev <= dfhighprevEMA):
				# CHECK IF SYMBOL IS NOT IN ORDERS THEN MAKE A BUY ORDER
				if(ex.symbolExistsOrders(orders, pair['symbol']) == False):

					buyOrder = ex.buyMarket(pair['symbol'], amount)

					orders.append({
						'orderID': buyOrder['orderId'],
						'symbol': buyOrder['symbol'],
						'buyPrice': buyOrder['price'],
						'sellID': 0,
						'sellPrice': 0,
						'amount': buyOrder['executedQty'],
						'side': buyOrder['side'],
						'status': buyOrder['status'],
						'tickSize': pair['tickSize'],
						'time': int(time.time())
						})

					hlp.addLog(orders[-1])
					ws.Beep(1000, 100)

		# CHECK STATUS OF ORDERS
		for order in orders:
			activeOrder = ex.checkOrder(order['symbol'], order['orderID'])

			if(activeOrder['side'] == "BUY"):

				if(activeOrder['status'] == 'NEW' and localTime >= order['time'] + int(cfg['orderTimeout'])):
					ex.cancelOrder(order['symbol'], order['orderID'])
					order['status'] = 'CANCELLED'
					hlp.addLog(order)
					orders.remove(order)


				if(activeOrder['status'] == 'PARTIALLY_FILLED' and localTime >= order['time'] + int(cfg['orderTimeout'])):
					order['amount'] = str(activeOrder['executedQty'])
					order['status'] = 'PARTIALLY_FILLED'
					hlp.addLog(order)
					ex.cancelOrder(order['symbol'], order['orderID'])
					Trailingstop(order)
					orders.remove(order)

					ws.Beep(1000, 100)
					ws.Beep(1000, 100)


				if(activeOrder['status'] == "FILLED"):
					order['amount'] = str(activeOrder['executedQty'])
					order['status'] = 'FILLED'
					hlp.addLog(order)
					Trailingstop(order)
					orders.remove(order)

					ws.Beep(1000, 100)
					ws.Beep(1000, 100)

	print('-'*50)
	time.sleep(60)

