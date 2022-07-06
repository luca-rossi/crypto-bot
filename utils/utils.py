import numpy as np
from tradingview_ta import TA_Handler
from utils.const import Data

class Utils:
	'''
	Contains miscellaneous functions.
	'''

	def get_time_from_count(count):
		count *= 5
		days = count // (60 * 24)
		hours = (count % (60 * 24)) // 60
		minutes = (count % (60 * 24)) % 60
		return str(days) + 'd ' + str(hours) + 'h ' + str(minutes) + 'm'

	def get_tv_analysis():
		analysis = {}
		for interval in Data.ALL_TIMEFRAMES:
			analysis[interval] = TA_Handler(symbol="BNBUSDT", screener="crypto", exchange="BINANCE", interval=interval).get_analysis()
		return analysis

	def normalize_amount(amount):
		return amount / 1000000000000000000

	def sigmoid(x):
		return 1 / (1 + np.exp(-x))

	def format_price(x):
		return ("-$" if x < 0 else "$") + "{0:.2f}".format(abs(x))