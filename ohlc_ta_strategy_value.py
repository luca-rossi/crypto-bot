'''
Creates a dataset of technical indicators from a Binance OHLC dataset. Simulates bets based on the value of those indicators.
This is just an example with some indicators, others can be loaded from the ta library.
'''
# TODO move content to StrategyTA
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import ADXIndicator, EMAIndicator
from ta import add_all_ta_features
from utils.config import Files

# TODO in Const
PERIOD_1M = '1m'
PERIOD_15M = '15m'

# loading
df = pd.read_csv(Files.DATA_BINANCE_OHLC_5M, sep=',')
df.dropna(inplace=True)
print(df)
df = add_all_ta_features(df, open='open', high='high', low='low', close='close', volume='volume', fillna=True)
# time frames
df_periods = {}
# df_periods[PERIOD_1M] = pd.read_csv(Files.DATA_BINANCE_OHLC_1M, sep=',')
# df_periods[PERIOD_1M] = add_all_ta_features(df_periods[PERIOD_1M], open='open', high='high', low='low', close='close', volume='volume', fillna=True)
for i in range(3):
	period = PERIOD_15M + str(i)
	df_periods[period] = df.iloc[i::3, :]
	df_periods[period]['close'] = df['close']
	print(df_periods[period])
# rsi
#df['rsi'] = RSIIndicator(close=df['close'], window=3).rsi()
df['rsi'] = StochRSIIndicator(close=df['close'], window=3).stochrsi_k()
df['prev_rsi'] = df['rsi'].shift(1)
# df_periods[PERIOD_1M]['rsi_1m'] = RSIIndicator(close=df_periods[PERIOD_1M]['close'], window=3).rsi()
for i in range(3):
	period = PERIOD_15M + str(i)
	#df_periods[period]['rsi_15m'] = RSIIndicator(close=df_periods[period]['close'], window=3).rsi()
	# rsi_indicator = RSIIndicator(close=df_periods[period]['close'])
	df_periods[period]['rsi_15m'] = RSIIndicator(close=df_periods[period]['close']).rsi()
	df_periods[period]['stochrsi_15m'] = StochRSIIndicator(close=df_periods[period]['close']).stochrsi()
# adx
df['adx'] = ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=5).adx()
df['adx_pos'] = ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=5).adx_pos()
df['adx_neg'] = ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=5).adx_neg()
# df_periods[PERIOD_1M]['adx_1m'] = ADXIndicator(high=df_periods[PERIOD_1M]['high'], low=df_periods[PERIOD_1M]['low'], close=df_periods[PERIOD_1M]['close'], window=5).adx()
# for i in range(3):
# 	period = PERIOD_15M + str(i)
# 	df_periods[period]['adx_15m'] = ADXIndicator(high=df_periods[period]['high'], low=df_periods[period]['low'], close=df_periods[period]['close'], window=5).adx()
# ema
df['ema50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()
df['ema100'] = EMAIndicator(close=df['close'], window=100).ema_indicator()
df['ema200'] = EMAIndicator(close=df['close'], window=200).ema_indicator()
# df_periods[PERIOD_1M]['ema50_1m'] = EMAIndicator(close=df_periods[PERIOD_1M]['close'], window=50).ema_indicator()
# df_periods[PERIOD_1M]['ema100_1m'] = EMAIndicator(close=df_periods[PERIOD_1M]['close'], window=100).ema_indicator()
# df_periods[PERIOD_1M]['ema200_1m'] = EMAIndicator(close=df_periods[PERIOD_1M]['close'], window=200).ema_indicator()
for i in range(3):
	period = PERIOD_15M + str(i)
	df_periods[period]['ema50_15m'] = EMAIndicator(close=df_periods[period]['close'], window=50).ema_indicator()
	df_periods[period]['ema100_15m'] = EMAIndicator(close=df_periods[period]['close'], window=100).ema_indicator()
	df_periods[period]['ema200_15m'] = EMAIndicator(close=df_periods[period]['close'], window=200).ema_indicator()
# result
df['result'] = np.where((df['close'] > df['open']), 1, 0)
df['result'] = df['result'].shift(-1)
# strategy
df['pred'] = np.nan
signal_adx_repl_buy = (df['adx'] > 30) & (df['adx_pos'] > df['adx_neg'])
signal_adx_repl_sell = (df['adx'] > 30) & (df['adx_pos'] < df['adx_neg'])
signal_ema_repl_buy = (df['ema50'] < df['ema100']) & (df['ema100'] < df['ema200'])
signal_ema_repl_sell = (df['ema50'] > df['ema100']) & (df['ema100'] > df['ema200'])
signal_buy = signal_adx_repl_buy & signal_ema_repl_buy
signal_sell = signal_adx_repl_sell & signal_ema_repl_sell
df.loc[signal_sell, 'pred'] = 0
df.loc[signal_buy, 'pred'] = 1
# evaluation
correct = df[df['result'] == df['pred']]['pred'].count()
tot_pred = df['pred'].count()
tot_res = df['result'].count()
accuracy = correct / tot_pred
tradable = tot_pred / tot_res
print(df)
print('Accuracy: ' + str(round(accuracy, 2)))
print('Tradable: ' + str(round(tradable, 4)))
df.to_csv(Files.DATA_BINANCE_OHLC_5M)
