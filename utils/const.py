from enum import Enum, auto
from tradingview_ta import Interval

class Const:
	INF = 1000000
	ROUND_DURATION = 300

class Transactions:
	BET_BULL = 'BetBull'
	BET_BEAR = 'BetBear'
	CLAIM = 'Claim'

class ContractMethods:
	# BNB
	BULL_METHOD = '0x57fb096f'
	BEAR_METHOD = '0xaa6b873a'
	CLAIM_METHOD = '0x6ba4c138'
	# CAKE
	# BULL_METHOD = '0x3923e1b4'
	# BEAR_METHOD = '0x0e89e5a4'
	# CLAIM_METHOD = '0x6ba4c138'

class Data:
	TIMEFRAMES = ['1m', '5m', '15m']
	ALL_TIMEFRAMES = [Interval.INTERVAL_1_MINUTE, Interval.INTERVAL_5_MINUTES, Interval.INTERVAL_15_MINUTES, Interval.INTERVAL_30_MINUTES, Interval.INTERVAL_1_HOUR, Interval.INTERVAL_2_HOURS, Interval.INTERVAL_4_HOURS, Interval.INTERVAL_1_DAY, Interval.INTERVAL_1_WEEK, Interval.INTERVAL_1_MONTH]
	TYPES = ['oscillators', 'moving_averages']
	COLUMNS_EPOCHS = ['epoch', 'start_time', 'end_time', 'lock_price', 'close_price', 'bull_amount', 'bear_amount']	#, 'indicators_saved', 'result'
	COLUMNS_TXS = ['blockNumber', 'timeStamp', 'from', 'value', 'input', 'epoch', 'start_time', 'time']


class IndicatorAnalysis:
	ANALYSIS_REC = [
		'RSI', 'STOCH.K', 'CCI', 'ADX', 'AO', 'Mom', 'MACD', 'Stoch.RSI', 'W%R', 'BBP', 'UO',
		'EMA10', 'SMA10', 'EMA20', 'SMA20', 'EMA30', 'SMA30', 'EMA50', 'SMA50', 'EMA100', 'SMA100',
		'EMA200', 'SMA200', 'Ichimoku', 'VWMA', 'HullMA'
	]
	ANALYSIS_IND = [
		'v_Recommend.Other', 'v_Recommend.All', 'v_Recommend.MA',
		'v_RSI', 'v_RSI[1]', 'v_Stoch.K', 'v_Stoch.D', 'v_Stoch.K[1]', 'v_Stoch.D[1]', 'v_CCI20', 'v_CCI20[1]',
		'v_ADX', 'v_ADX+DI', 'v_ADX-DI', 'v_ADX+DI[1]', 'v_ADX-DI[1]',
		'v_AO', 'v_AO[1]', 'v_AO[2]', 'v_Mom', 'v_Mom[1]', 'v_MACD.macd', 'v_MACD.signal',
		'v_Stoch.RSI.K', 'v_W.R', 'v_BBPower', 'v_UO', 'v_P.SAR', 'v_BB.lower', 'v_BB.upper',
		'v_close', 'v_open', 'v_low', 'v_high', 'v_change',
		'v_EMA5', 'v_SMA5', 'v_EMA10', 'v_SMA10', 'v_EMA20', 'v_SMA20', 'v_EMA30', 'v_SMA30',
		'v_EMA50', 'v_SMA50', 'v_EMA100', 'v_SMA100', 'v_EMA200', 'v_SMA200', 'v_Ichimoku.BLine', 'v_VWMA', 'v_HullMA9'
	]
	ANALYSIS_IND_NORM_100 = [
		'v_RSI', 'v_RSI[1]', 'v_Stoch.K', 'v_Stoch.D', 'v_Stoch.K[1]', 'v_Stoch.D[1]', 'v_CCI20', 'v_CCI20[1]',
		'v_ADX', 'v_ADX+DI', 'v_ADX-DI', 'v_ADX+DI[1]', 'v_ADX-DI[1]',
		'v_Stoch.RSI.K', 'v_W.R', 'v_UO', 'v_P.SAR', 'v_BB.lower', 'v_BB.upper'
	]
	ANALYSIS_IND_NORM_PRICE = [
		'v_close', 'v_open', 'v_low', 'v_high',
		'v_EMA5', 'v_SMA5', 'v_EMA10', 'v_SMA10', 'v_EMA20', 'v_SMA20', 'v_EMA30', 'v_SMA30',
		'v_EMA50', 'v_SMA50', 'v_EMA100', 'v_SMA100', 'v_EMA200', 'v_SMA200', 'v_Ichimoku.BLine', 'v_VWMA', 'v_HullMA9'
	]

# options
class SimLogOptions(Enum):
	MINIMAL = auto()
	EPOCHS = auto()
	WINDOW = auto()
	CSV = auto()
	SAVE_WINDOW = auto()

class BotLogOptions(Enum):
	CONSOLE = auto()
	SAVE_EAGER = auto()
	SAVE_LAZY = auto()

class BotModes(Enum):
	INIT_FIRST = auto()
	INIT = auto()
	CHILL = auto()
	FOCUS = auto()

class IndicatorPreds(Enum):
	IGNORE = auto()
	OKAY = auto()
	BET_BULL = auto()
	BET_BEAR = auto()
	NEUTRAL = auto()
