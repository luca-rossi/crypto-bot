from utils.const import Transactions
from utils.utils import Utils

class StrategyTA:
	'''
	Contains the strategies based on technical analysis.
	'''
	params = None

	def get_ta_bet(analysis):
		'''
		Old strategy based on technical analysis.
		'''
		analysis = Utils.get_tv_analysis()
		ema50_1m = analysis['1m'].indicators['EMA50']
		ema100_1m = analysis['1m'].indicators['EMA100']
		ema200_1m = analysis['1m'].indicators['EMA200']
		custom_trend_1m = 'NEUTRAL'
		if ema50_1m > ema100_1m and ema100_1m > ema200_1m:
			custom_trend_1m = 'BUY'
		elif ema50_1m < ema100_1m and ema100_1m < ema200_1m:
			custom_trend_1m = 'SELL'
		adx_pos_5m = analysis['5m'].indicators['ADX+DI']
		adx_neg_5m = analysis['5m'].indicators['ADX-DI']
		adx_safe_5m = 'BUY' if adx_pos_5m > adx_neg_5m else 'SELL'
		if abs(adx_pos_5m - adx_neg_5m) < 0.2:
			adx_safe_5m = 'NEUTRAL'
		# TODO params outside of this function
		indicators = [
			# analysis['15m'].oscillators['COMPUTE']['Stoch.RSI'],
		]
		indicators_rev = [
			analysis['15m'].oscillators['COMPUTE']['MACD'],
		]
		indicators_ignore_n = [
			analysis['15m'].oscillators['COMPUTE']['Stoch.RSI'],
		]
		indicators_ignore_bs = [
			analysis['1m'].oscillators['COMPUTE']['CCI'],
		]
		bet_bull = True
		bet_bear = True
		for indicator in indicators:
			if indicator != 'SELL':
				bet_bear = False
			if indicator != 'BUY':
				bet_bull = False
		for indicator in indicators_rev:
			if indicator != 'SELL':
				bet_bull = False
			if indicator != 'BUY':
				bet_bear = False
		for indicator in indicators_ignore_n:
			if indicator == 'NEUTRAL':
				bet_bull = False
				bet_bear = False
		for indicator in indicators_ignore_bs:
			if indicator != 'NEUTRAL':
				bet_bull = False
				bet_bear = False
		return Transactions.BET_BULL if bet_bull else (Transactions.BET_BEAR if bet_bear else None), analysis
