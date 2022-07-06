'''
Creates a dataset of technical indicators from a Binance OHLC dataset. Simulates bets based on signals generated from those indicators.
This is just an example with some indicators, others can be loaded from the ta library.
'''
# TODO move content to StrategyTA
import pandas as pd
import numpy as np
from ta.utils import dropna
from ta.momentum import StochRSIIndicator
from ta.trend import ADXIndicator, EMAIndicator
from utils.config import Files

# loading
df = pd.read_csv(Files.DATA_BINANCE_OHLC_5M, sep=',')
df.dropna(inplace=True)
print(df)
# df = add_all_ta_features(df, open='open', high='high', low='low', close='close', volume='volume', fillna=True)
# 15 min dataframe
df15 = {}
for i in range(3):
	df15[i] = df.iloc[i::3, :]
	df15[i]['close'] = df['close']
	print(df15[i])
# rsi
df['rsi'] = StochRSIIndicator(close=df['close']).stochrsi()		# blue
df['rsi_k'] = StochRSIIndicator(close=df['close']).stochrsi_k()		# blue
df['rsi_d'] = StochRSIIndicator(close=df['close']).stochrsi_d()		# red
df['prev_rsi'] = df['rsi'].shift(4)
df['prev_rsi_k'] = df['rsi_k'].shift(4)
df['prev_rsi_d'] = df['rsi_d'].shift(4)
# df['diff_rsi_k'] = df['rsi_k'] - df['prev_rsi_k']
# df['diff_rsi_d'] = df['rsi_d'] - df['prev_rsi_d']
for i in range(3):
	df15[i]['rsi_15m'] = StochRSIIndicator(close=df15[i]['close']).stochrsi()
	df15[i]['rsi_k_15m'] = StochRSIIndicator(close=df15[i]['close']).stochrsi_k()
	df15[i]['rsi_d_15m'] = StochRSIIndicator(close=df15[i]['close']).stochrsi_d()
df['rsi_15m_w'] = StochRSIIndicator(close=df['close']).stochrsi()
df['rsi_k_15m_w'] = StochRSIIndicator(close=df['close']).stochrsi_k()
df['rsi_d_15m_w'] = StochRSIIndicator(close=df['close']).stochrsi_d()
df['prev_rsi_15m_w'] = df['rsi_15m_w'].shift(4)
df['prev_rsi_k_15m_w'] = df['rsi_k_15m_w'].shift(4)
df['prev_rsi_d_15m_w'] = df['rsi_d_15m_w'].shift(4)
df['rsi_15m'] = np.nan
df['rsi_k_15m'] = np.nan
df['rsi_d_15m'] = np.nan
df['prev_rsi_15m'] = np.nan
df['prev_rsi_k_15m'] = np.nan
df['prev_rsi_d_15m'] = np.nan
for i in range(3):
	df['rsi_15m'] = df['rsi_15m'].fillna(df15[i]['rsi_15m'])
	df['rsi_k_15m'] = df['rsi_k_15m'].fillna(df15[i]['rsi_k_15m'])
	df['rsi_d_15m'] = df['rsi_d_15m'].fillna(df15[i]['rsi_d_15m'])
df['prev_rsi_15m'] = df['rsi_15m'].shift(4)
df['prev_rsi_k_15m'] = df['rsi_k_15m'].shift(4)
df['prev_rsi_d_15m'] = df['rsi_d_15m'].shift(4)
# adx
adx_indicator = ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=5)
# df['adx'] = adx_indicator.adx()
df['adx_pos'] = adx_indicator.adx_pos()
df['adx_neg'] = adx_indicator.adx_neg()
di = 100 * abs(df['adx_pos'] - df['adx_neg']) / (df['adx_pos'] + df['adx_neg'])
df['adx'] = di.rolling(window=5).mean()
df['prev_adx_pos'] = df['adx_pos'].shift(4)
df['prev_adx_neg'] = df['adx_neg'].shift(4)
df['prev_adx'] = df['adx'].shift(4)
# df['diff_adx_pos'] = df['adx_pos'] - df['prev_adx_pos']
# df['diff_adx_neg'] = df['adx_neg'] - df['prev_adx_neg']
# df['diff_adx_di'] = df['adx_pos'] - df['adx_neg']
# df['diff_adx'] = df['adx'] - df['prev_adx']
# ema
df['ema50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()
df['ema100'] = EMAIndicator(close=df['close'], window=100).ema_indicator()
df['ema200'] = EMAIndicator(close=df['close'], window=200).ema_indicator()
df['ratio_ema50'] = df['ema50'] / df['close']
df['ratio_ema100'] = df['ema100'] / df['ema50']
df['ratio_ema200'] = df['ema200'] / df['ema100']
# result
df['result'] = np.where((df['close'] > df['open']), 1, 0)
df['result'] = df['result'].shift(-1)
print(df)
# strategy
df['pred'] = np.nan
signal_rsi_buy = (df['rsi_15m'] > 0.20) & (df['prev_rsi_15m'] < 0.20)
signal_rsi_sell = (df['rsi_15m'] < 0.80) & (df['prev_rsi_15m'] > 0.80)
signal_ema_buy = (df['low'] > df['ema50'])
signal_ema_sell = (df['high'] < df['ema50'])
diff = df['adx_pos'] - df['adx_neg']
prev_diff = df['prev_adx_pos'] - df['prev_adx_neg']
signal_adx_buy = (diff > 0) & (prev_diff < 0) & (df['adx'] > 30)
signal_adx_sell = (diff < 0) & (prev_diff > 0) & (df['adx'] > 30)
signal_buy = signal_rsi_buy & signal_adx_buy & signal_ema_buy
signal_sell = signal_rsi_sell & signal_adx_sell & signal_ema_sell
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
