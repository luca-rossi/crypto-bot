import pandas as pd
import math
import os.path
from binance.client import Client
from datetime import datetime
from utils.config import Blockchain

class BinanceLoader:
	'''
	Loads historical price data from Binance (without indicators).
	This allows to make experiments on a large amount of data, but it's Binance data, not PS.
	This is useful to test strategies not specific to prediction, but indicators have to be implemented.
	'''

	def load(self, filename, symbol='BNBUSDT', candle='1m', remote=False):
		'''
		Loads the binance history remotely or locally (from a csv file).
		'''
		if remote:
			# TODO move in Const
			BIN_SIZES = {"1m": 1, "5m": 5, "1h": 60, "1d": 1440}
			binance_client = Client(api_key=Blockchain.BINANCE_API_KEY, api_secret=Blockchain.BINANCE_API_PRIVATE_KEY)
			if os.path.isfile(filename):
				data_df = pd.read_csv(filename)
			else:
				data_df = pd.DataFrame()
			# get minutes of new data
			oldest_point = datetime.strptime('1 Jan 2021', '%d %b %Y')
			newest_point = pd.to_datetime(binance_client.get_klines(symbol, interval=candle)[-1][0], unit='ms')
			delta_min = (newest_point - oldest_point).total_seconds() / 60
			available_data = math.ceil(delta_min / BIN_SIZES[candle])
			if oldest_point == datetime.strptime('1 Jan 2017', '%d %b %Y'):
				print('Downloading all available ' + candle + ' data for ' + symbol + '....')
			else:
				print('Downloading ' + delta_min + ' minutes of new data available for ' + symbol + ', i.e. ' + available_data + ' instances of ' + candle + ' data...')
			klines = binance_client.get_historical_klines(symbol, candle, oldest_point.strftime("%d %b %Y %H:%M:%S"), newest_point.strftime("%d %b %Y %H:%M:%S"))
			data = pd.DataFrame(klines, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
			data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
			if len(data_df) > 0:
				temp_df = pd.DataFrame(data)
				data_df = data_df.append(temp_df)
			else:
				data_df = data
			data_df.set_index('timestamp', inplace=True)
			data_df.to_csv(filename)
			print('Done!')
			return data_df
		df = pd.read_csv(filename)
		df = df.loc[:, ['timestamp', 'close']]
		df['timestamp'] = pd.to_datetime(df['timestamp'])
		return df
