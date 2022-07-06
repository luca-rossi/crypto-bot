'''
Creates a dataset of technical indicators from a Binance OHLC dataset.
This is just an example with some indicators, others can be loaded from the ta library.
'''
# TODO move content to StrategyTA
import pandas as pd
import numpy as np
from ta.momentum import StochRSIIndicator
from ta.trend import ADXIndicator, EMAIndicator, SMAIndicator, MACD
from ta import add_all_ta_features
from utils.config import Files

# loading
df = pd.read_csv(Files.DATA_BINANCE_OHLC_5M, sep=',')
df.dropna(inplace=True)
print(df)
df = add_all_ta_features(df, open='open', high='high', low='low', close='close', volume='volume', fillna=True)
# 15 min dataframe
df15 = {}
for i in range(3):
	df15[i] = df.iloc[i::3, :]
	df15[i]['close'] = df['close']
	print(df15[i])
# rsi
df['rsi_k'] = StochRSIIndicator(close=df['close'], window=3).stochrsi_k()		# blue
df['rsi_d'] = StochRSIIndicator(close=df['close'], window=3).stochrsi_d()		# red
df['prev_rsi_k'] = df['rsi_k'].shift(1)
df['prev_rsi_d'] = df['rsi_d'].shift(1)
df['prev2_rsi_k'] = df['rsi_k'].shift(2)
df['prev2_rsi_d'] = df['rsi_d'].shift(2)
for i in range(3):
	df15[i]['rsi_k_15m'] = StochRSIIndicator(close=df15[i]['close'], window=3).stochrsi_k()
	df15[i]['rsi_d_15m'] = StochRSIIndicator(close=df15[i]['close'], window=3).stochrsi_d()
df['rsi_k_14'] = StochRSIIndicator(close=df['close'], window=14).stochrsi_k()
df['rsi_d_14'] = StochRSIIndicator(close=df['close'], window=14).stochrsi_d()
df['prev_rsi_k_14'] = df['rsi_k_14'].shift(1)
df['prev_rsi_d_14'] = df['rsi_d_14'].shift(1)
df['prev2_rsi_k_14'] = df['rsi_k_14'].shift(2)
df['prev2_rsi_d_14'] = df['rsi_d_14'].shift(2)
# adx 5
adx_indicator = ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=5)
df['adx_pos'] = adx_indicator.adx_pos()
df['adx_neg'] = adx_indicator.adx_neg()
df['prev_adx_pos'] = df['adx_pos'].shift(1)
df['prev_adx_neg'] = df['adx_neg'].shift(1)
# adx 14
adx14_indicator = ADXIndicator(high=df['high'], low=df['low'], close=df['close'])
df['adx14_pos'] = adx14_indicator.adx_pos()
df['adx14_neg'] = adx14_indicator.adx_neg()
df['prev_adx14_pos'] = df['adx14_pos'].shift(1)
df['prev_adx14_neg'] = df['adx14_neg'].shift(1)
df['prev2_adx14_pos'] = df['adx14_pos'].shift(2)
df['prev2_adx14_neg'] = df['adx14_neg'].shift(2)
# ema
df['ema50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()
df['ema100'] = EMAIndicator(close=df['close'], window=100).ema_indicator()
df['ema200'] = EMAIndicator(close=df['close'], window=200).ema_indicator()
df['sma600'] = SMAIndicator(close=df['close'], window=600).sma_indicator()
df['ratio_ema50_close'] = df['ema50'] / df['close']
df['ratio_ema100_50'] = df['ema100'] / df['ema50']
df['ratio_ema200_100'] = df['ema200'] / df['ema100']
df['ratio_sma600_close'] = df['sma600'] / df['close']
# macd
df['macd_diff'] = MACD(close=df['close']).macd_diff()
df['prev_macd_diff'] = df['macd_diff'].shift(1)
# result
df['temp_result'] = np.where((df['close'] > df['open']), 1, 0)
df['prev_result'] = df['temp_result'].shift(1)
df['temp_result'] = 100 * (1 - df['close'] / df['open'])
df['result'] = df['temp_result'].shift(-1)
df = df.drop(['temp_result', 'ema50', 'ema100', 'ema200', 'sma600', 'timestamp', 'open', 'high', 'low', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'], axis=1)
print(df)
df.to_csv(Files.DATA_BINANCE_OHLC_5M)
