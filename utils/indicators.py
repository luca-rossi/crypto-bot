'''
The following functions generate extra technical indicators other than the tradingview recommendations.
The "strategy" indicator is a special indicator that refers to the strategy based on expected payout.
'''
# TODO consider removing the strategy indicator and selecting between different strategies earlier in the process

import pandas as pd
from modules.strategies.strategy import Strategy
from utils.const import IndicatorPreds

def custom_rec_osc(epoch_data, epoch_inds, tf):
	K = 0
	df = custom_adx(epoch_data, epoch_inds, tf)
	rec = epoch_inds['Recommend.Other_' + tf]
	df.loc[:] = IndicatorPreds.NEUTRAL
	df.loc[rec > K] = IndicatorPreds.BET_BULL
	df.loc[rec < -K] = IndicatorPreds.BET_BEAR
	return df

def custom_rec_osc_strict(epoch_data, epoch_inds, tf):
	K = 0.1
	df = custom_adx(epoch_data, epoch_inds, tf)
	rec = epoch_inds['Recommend.Other_' + tf]
	df.loc[:] = IndicatorPreds.NEUTRAL
	df.loc[rec > K] = IndicatorPreds.BET_BULL
	df.loc[rec < -K] = IndicatorPreds.BET_BEAR
	return df

def custom_rec_osc_ultra_strict(epoch_data, epoch_inds, tf):
	K = 0.15
	df = custom_adx(epoch_data, epoch_inds, tf)
	rec = epoch_inds['Recommend.Other_' + tf]
	df.loc[:] = IndicatorPreds.NEUTRAL
	df.loc[rec > K] = IndicatorPreds.BET_BULL
	df.loc[rec < -K] = IndicatorPreds.BET_BEAR
	return df

def custom_rsi(epoch_data, epoch_inds, tf):
	stoch_k = epoch_inds['Stoch.K_' + tf]
	stoch_d = epoch_inds['Stoch.D_' + tf]
	df = pd.Series().reindex_like(epoch_inds)
	df.loc[stoch_k > stoch_d] = IndicatorPreds.BET_BULL
	df.loc[stoch_k < stoch_d] = IndicatorPreds.BET_BEAR
	df.loc[stoch_k == stoch_d] = IndicatorPreds.NEUTRAL
	return df

def custom_rsi_safe(epoch_data, epoch_inds, tf):
	df = custom_rsi(epoch_data, epoch_inds, tf)
	stoch_k = epoch_inds['Stoch.K_' + tf]
	df.loc[(stoch_k > 80) | (stoch_k < 20)] = IndicatorPreds.NEUTRAL
	return df

def custom_rsi_ultrasafe(epoch_data, epoch_inds, tf):
	df = custom_rsi(epoch_data, epoch_inds, tf)
	stoch_k = epoch_inds['Stoch.K_' + tf]
	df.loc[(stoch_k > 70) | (stoch_k < 30)] = IndicatorPreds.NEUTRAL
	return df

def custom_trend(epoch_data, epoch_inds, tf):
	ema50 = epoch_inds['EMA50_' + tf]
	ema100 = epoch_inds['EMA100_' + tf]
	ema200 = epoch_inds['EMA200_' + tf]
	df = pd.Series().reindex_like(epoch_inds)
	df.loc[:] = IndicatorPreds.NEUTRAL
	df.loc[(ema50 > ema100) & (ema100 > ema200)] = IndicatorPreds.BET_BULL
	df.loc[(ema50 < ema100) & (ema100 < ema200)] = IndicatorPreds.BET_BEAR
	return df

def custom_trend_super(epoch_data, epoch_inds, tf):
	lock_price = epoch_data['lock_price']
	ema50 = epoch_inds['EMA50_' + tf]
	ema100 = epoch_inds['EMA100_' + tf]
	ema200 = epoch_inds['EMA200_' + tf]
	df = pd.Series().reindex_like(epoch_inds)
	df.loc[:] = IndicatorPreds.NEUTRAL
	df.loc[(lock_price > ema50) & (ema50 > ema100) & (ema100 > ema200)] = IndicatorPreds.BET_BULL
	df.loc[(lock_price < ema50) & (ema50 < ema100) & (ema100 < ema200)] = IndicatorPreds.BET_BEAR
	return df

def custom_adx(epoch_data, epoch_inds, tf):
	adx_pos = epoch_inds['ADX+DI_' + tf]
	adx_neg = epoch_inds['ADX-DI_' + tf]
	df = pd.Series().reindex_like(epoch_inds)
	df.loc[adx_pos > adx_neg] = IndicatorPreds.BET_BULL
	df.loc[adx_pos < adx_neg] = IndicatorPreds.BET_BEAR
	df.loc[adx_pos == adx_neg] = IndicatorPreds.NEUTRAL
	return df

def custom_adx_safe(epoch_data, epoch_inds, tf):
	df = custom_adx(epoch_data, epoch_inds, tf)
	adx_pos = epoch_inds['ADX+DI_' + tf]
	adx_neg = epoch_inds['ADX-DI_' + tf]
	df.loc[adx_pos - adx_neg < 0.2] = IndicatorPreds.NEUTRAL
	return df

def custom_bbp(epoch_data, epoch_inds, tf):
	bbp = epoch_inds['BBPower_' + tf]
	df = pd.Series().reindex_like(epoch_inds)
	df.loc[bbp > 0] = IndicatorPreds.BET_BULL
	df.loc[bbp < 0] = IndicatorPreds.BET_BEAR
	df.loc[bbp == 0] = IndicatorPreds.NEUTRAL
	return df

def custom_macd(epoch_data, epoch_inds, tf):
	macd_m = epoch_inds['MACD.macd_' + tf]
	macd_s = epoch_inds['MACD.signal_' + tf]
	df = pd.Series().reindex_like(epoch_inds)
	df.loc[macd_m > macd_s] = IndicatorPreds.BET_BULL
	df.loc[macd_m < macd_s] = IndicatorPreds.BET_BEAR
	df.loc[macd_m == macd_s] = IndicatorPreds.NEUTRAL
	return df

def custom_macd_safe(epoch_data, epoch_inds, tf):
	macd_m = epoch_inds['MACD.macd_' + tf]
	macd_s = epoch_inds['MACD.signal_' + tf]
	df = pd.Series().reindex_like(epoch_inds)
	df.loc[:] = IndicatorPreds.NEUTRAL
	df.loc[(macd_m > macd_s) & (macd_m > 0)] = IndicatorPreds.BET_BULL
	df.loc[(macd_m < macd_s) & (macd_m < 0)] = IndicatorPreds.BET_BEAR
	return df

def __custom_crossover(epoch_data, epoch_inds, tf, short_interval, long_interval):
	epoch_inds = epoch_inds.copy().reindex(list(range(int(epoch_inds.index.min()), int(epoch_inds.index.max()) + 1)))
	prev_short = epoch_inds[short_interval + '_' + tf].shift(1)
	prev_long = epoch_inds[long_interval + '_' + tf].shift(1)
	curr_short = epoch_inds[short_interval + '_' + tf]
	curr_long = epoch_inds[long_interval + '_' + tf]
	df = pd.Series().reindex_like(epoch_inds)
	df.loc[:] = IndicatorPreds.NEUTRAL
	df.loc[(prev_short < prev_long) & (curr_short > curr_long)] = IndicatorPreds.BET_BULL
	df.loc[(prev_short > prev_long) & (curr_short < curr_long)] = IndicatorPreds.BET_BEAR
	return df

def custom_ema_crossover_1020(epoch_data, epoch_inds, tf):
	return __custom_crossover(epoch_data, epoch_inds, tf, 'EMA10', 'EMA20')

def custom_ema_crossover_1050(epoch_data, epoch_inds, tf):
	return __custom_crossover(epoch_data, epoch_inds, tf, 'EMA10', 'EMA50')

def custom_ema_crossover_2050(epoch_data, epoch_inds, tf):
	return __custom_crossover(epoch_data, epoch_inds, tf, 'EMA20', 'EMA50')

def strategy(epoch_data, epoch_inds, tf):
	df = pd.Series().reindex_like(epoch_inds)
	df.loc[:] = IndicatorPreds.NEUTRAL
	filter_bullish, filter_bearish = Strategy.get_simulator_strategy(epoch_data, epoch_inds, tf)
	df.loc[filter_bullish & (~filter_bearish)] = IndicatorPreds.BET_BULL
	df.loc[filter_bearish & (~filter_bullish)] = IndicatorPreds.BET_BEAR
	return df

INDICATORS = {
	'custom_rec_osc': custom_rec_osc,
	'custom_rec_osc_strict': custom_rec_osc_strict,
	'custom_rec_osc_ultra_strict': custom_rec_osc_ultra_strict,
	'custom_rsi': custom_rsi,
	'custom_rsi_safe': custom_rsi_safe,
	'custom_rsi_ultrasafe': custom_rsi_ultrasafe,
	'custom_trend': custom_trend,
	'custom_trend_super': custom_trend_super,
	'custom_adx': custom_adx,
	'custom_adx_safe': custom_adx_safe,
	'custom_bbp': custom_bbp,
	'custom_macd': custom_macd,
	'custom_macd_safe': custom_macd_safe,
	'custom_ema_crossover_1020': custom_ema_crossover_1020,
	'custom_ema_crossover_1050': custom_ema_crossover_1050,
	'custom_ema_crossover_2050': custom_ema_crossover_2050,
	'strategy': strategy,
}
