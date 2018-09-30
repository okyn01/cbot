import backtrader.feeds as btfeeds
import backtrader as bt
import pandas as pd
import talib as ta


class PandasExtend(btfeeds.PandasData):
	lines = ('haopenema', 'hacloseema', 'halowema', 'hahighema')
	params = (
						('haopenema', -1),
						('hacloseema', -1),
						('halowema', -1),
						('hahighema', -1)
						)

	datafields = btfeeds.PandasData.datafields + (['haopenema', 'hacloseema', 'halowema', 'hahighema'])

def ha(ohcl, len1=10, len2=10):
	ohcl['OpenEMA'] = ta.EMA(ohcl.Open.values, timeperiod=len1)
	ohcl['HighEMA'] = ta.EMA(ohcl.High.values, timeperiod=len1)
	ohcl['LowEMA'] = ta.EMA(ohcl.Low.values, timeperiod=len1)
	ohcl['CloseEMA'] = ta.EMA(ohcl.Close.values, timeperiod=len1)

	ohcl.dropna(inplace=True)

	# Create the haikin ashi candles
	ohcl['HA_Close'] = (ohcl['OpenEMA'] + ohcl['HighEMA'] + ohcl['LowEMA'] + ohcl['CloseEMA']) / 4
	
	ohcl['HA_Open'] = ohcl['OpenEMA'][0:1] # set first HA_Open equal to first open
	previoushaopen = None
	previoushaclose = None
	for index, row in ohcl.iterrows():
		if(previoushaopen and previoushaclose):
			ohcl.loc[index, 'HA_Open'] = (previoushaopen + previoushaclose) / 2
		previoushaopen = ohcl.loc[index, 'HA_Open']
		previoushaclose = ohcl.loc[index, 'HA_Close']

	ohcl['HA_High']=ohcl[['HA_Open','HA_Close','HighEMA']].max(axis=1)
	ohcl['HA_Low']=ohcl[['HA_Open','HA_Close','LowEMA']].min(axis=1)


	ohcl['haopenema'] = ta.EMA(ohcl.HA_Open.values, timeperiod=len2)
	ohcl['hahighema'] = ta.EMA(ohcl.HA_High.values, timeperiod=len2)
	ohcl['halowema'] = ta.EMA(ohcl.HA_Low.values, timeperiod=len2)
	ohcl['hacloseema'] = ta.EMA(ohcl.HA_Close.values, timeperiod=len2)

	ohcl.dropna(inplace=True)

	return ohcl


# Create a Stratey
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.dataclose = self.datas[0].close
        self.datalow = self.datas[0].low

        self.emaopen = self.datas[0].haopenema
        self.emahigh = self.datas[0].hahighema
        self.emaclose = self.datas[0].hacloseema
        self.emalow = self.datas[0].halowema


        self.deviation = 2
        self.stopLoss = 1


        self.ema = bt.indicators.SMA(self.data.close, period=200)

        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
                self.buyPrice = order.executed.price
                self.higherHigh = order.executed.price
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)


        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        #self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            #if(self.emaopen[0] <= self.emaclose[0] and self.emaopen[-1] >= self.emaclose[-1] and self.ema < self.dataclose):
            if(self.datahigh[0] >= self.emahigh[0] and self.datahigh[-1] <= self.emahigh[-1] and self.ema[0] < self.dataclose[0]):
            # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.buysize = (10000/self.data.close*0.70)
                self.order = self.buy(size=self.buysize)

        else:
            #set a new higher high
            if(self.higherHigh < self.dataclose[0]):
                self.higherHigh = self.dataclose[0]

            if(self.dataclose[0] < self.higherHigh * (1 - (self.deviation / 100))):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell(size=self.buysize)




df = pd.read_json('data\\Binance_BTCUSDT_5m_15 Jul, 2018-26 Sep, 2018.json')
df.columns = ['date', 'Open', 'High', 'Low', 'Close', 'volume', 'timeClose', 'QAS', 'NoT', 'TBA', 'TBQ', 'ignore']
del df['QAS'], df['NoT'], df['TBA'], df['TBQ'], df['ignore']
df['date'] = pd.to_datetime(df['date'],unit='ms')
df.set_index('date', inplace=True)

hadataset = ha(df)

cerebro = bt.Cerebro()
cerebro.addstrategy(TestStrategy)

cerebro.broker.setcash(10000.0)
cerebro.broker.setcommission(commission=0.00075)

data = PandasExtend(dataname=hadataset)
cerebro.adddata(data)

print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.run()

print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.plot()
