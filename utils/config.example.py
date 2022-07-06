# TODO most of these should become args, remove unused ones
from utils.const import Const

class Blockchain:
	BINANCE_API_KEY = '[YOUR BINANCE API KEY HERE]'
	HTTP_NODE = 'https://bsc-dataseed1.binance.org'
	ADDRESS = '[YOUR BSC ADDRESS HERE]'
	CONTRACT_ADDRESS = '0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA'
	GAS = 400000
	GWEI = 1000000000
	MAX_GAS_PRICE = 10.5 * GWEI
	MIN_GAS_PRICE = 6.5 * GWEI
	TIMEOUT = 5							# for API calls
	# **DANGER ZONE** - DO NOT SHARE THESE WITH ANYONE!
	BINANCE_API_PRIVATE_KEY = '[YOUR BINANCE API PRIVATE KEY HERE]'
	WALLET_PRIVATE_KEY = '[YOUR BSC ADDRESS PRIVATE KEY HERE]'
	BSCSCAN_KEY = '[YOUR BSCSCAN KEY HERE]'

class Files:
	# logs
	LOG_EPOCHS = 'logs/epochs.csv'
	LOG_TXS = 'logs/tx_history.csv'
	LOG_HISTORY_REC = 'logs/history_rec.csv'
	LOG_HISTORY_IND = 'logs/history_ind.csv'
	LOG_HISTORY_REC_ALL = 'logs/history_rec_all.csv'
	LOG_HISTORY_IND_ALL = 'logs/history_ind_all.csv'
	LOG_BOT = 'logs/botlog.txt'
	LOG_WINDOW = 'bot_window.txt'
	# file splits
	SPLIT_FILES = ['logs/history_rec.csv', 'logs/history_ind.csv']
	SPLIT_FILES_ALL = ['logs/history_rec_all.csv', 'logs/history_ind_all.csv']
	SPLIT_DIRS = ['pred_histories/pred_history_rec', 'pred_histories/pred_history_ind']
	SPLIT_DIRS_ALL = ['pred_histories/pred_history_rec_all', 'pred_histories/pred_history_ind_all']
	SPLIT_CHUNK_SIZE = 5000
	SPLIT_CHUNK_SIZE_ALL = 1000
	# data
	DATA_BINANCE_OHLC_1M = 'data/binance_ohlc_1m.csv'
	DATA_BINANCE_OHLC_5M = 'data/binance_ohlc_5m.csv'
	DATA_BINANCE_OHLC_5M_TREE = 'data/binance_ohlc_5m_tree.csv'
	DATA_EPOCHS = 'data/epochs.csv'
	DATA_WINDOW = 'data/data_window.csv'
	DATA_IND = 'data/data_ta_ind.csv'
	DATA_IND_OSC = 'data/data_ta_ind_osc.csv'
	DATA_PREP = 'data/test.csv'			# TODO temp
	# models
	MODEL = 'data/model.h5'
	MODEL_WINDOW = 'data/model_window.h5'
	MODEL_AGENT = 'data/agent_{}.h5'

class BotStrategy:
	# mode
	SILENT_MODE_KILL = False			# only checked during silent mode. If True, kill the bot after a certain number of transactions. Otherwise, an alarm will be triggered
	SILENT_MODE_MAX_TX = 50				# only checked during silent mode. It's the number of txs that will trigger the alarm (or kill the bot)
	# settings
	UPDATE_ATTEMPTS = 50				# number of attempts for updating epoch data to obtain bet result
	BLOCKS_OFFSET = 100
	MIN_TIME_FOR_TX = 5					# time constraint in seconds: a transaction takes about 12 seconds
	RUSH_TIME = 15						# don't sleep until finish
	FOCUS_TIME = 11#12					# finish asynchronous transition between chill mode and focus mode
	TX_TIME = 11						# do the transaction as late as possible (6-7 sec tx + 1-2 sec whale detection)
	SLEEP_TIME = 1
	SLACK_TIME = 31						# how many extra seconds the bot sleeps at the end of each round (30 seconds to update the round and epoch_data)
	MAX_SLEEP_TIME = 60
	N_BETS_TO_CLAIM = 1
	BET_AMOUNT = 0.03					# ***CHANGE WITH EXTREME CAUTION!***
	# window strategy - this is just the window strategy (ran by the simulator); to change the real strategy, implement it in main.py
	INDICATORS = ['rev_MACD_15m', 'ignore_n_Stoch.RSI_15m', 'ignore_bs_CCI_1m']
	WINDOW_DATA = {
		'min_payout_accuracy': 0.15,
		'max_payout_accuracy': 0.95,
		'min_window_accuracy': 0.30,
		'max_var': 100000,
		'bet_win_window_weight': 43,
		'bet_loss_window_weight': 37,
		'payout_smoothing': 5,
		'window_smoothing': 8,
		'payout_window': 12,
		'var_window': 50,
		'my_window': 435,
		'switch_mode': False
	}

class SimulatorSettings:
	MIN_EPOCH = 0
	INIT_BALANCE = 0
	MIN_BALANCE_RATIO = 0.8
	MAX_PAYOUT = Const.INF				# 3 is better unless using payout-based strategies
	BET_AMOUNT = 20
	BET_RATIO = 0.05
	FEE_ABS_BSC = 0.7
	FEE_ABS_BSC_CLAIM = 0.5
	FEE_REL_PS = 0.03
	FEE_TRADING = 0.0008				# percentage of the position x 2 (because it's paid when the position is closed too)
	DEFAULT_WINDOW_DATA = {
		'min_payout_accuracy': -Const.INF,
		'max_payout_accuracy': 1,		# ignore with 1
		'min_window_accuracy': -Const.INF,
		'max_var': Const.INF,
		'bet_win_window_weight': 8,
		'bet_loss_window_weight': 4,
		'payout_smoothing': 9,
		'window_smoothing': 0,
		'payout_window': 28,			# 288: 1 day
		'var_window': 50,
		'my_window': 23,				# 288: 1 day
		'switch_mode': False
	}
	# choose which columns to show in simulation:
	# - Basic info:			'bet_count', 'timestamp', 'time', 'win_bet', 'payout', 'bet', 'result', 'balance'
	# - Accuracy info:		'acc', 'wacc'
	# - Window info:		'avg_payout_acc', 'avg_window_acc', 'payout_var', 'var_window', 'winodw_payout'
	# - Tx info:			'amount_gap', 'whales_bet', 'tx_count', 'total_payout', 'tx_bull_votes', 'tx_bear_votes', 'tx_vote_gap'
	# - Loss streak info:	'loss_streak', 'loss_window', 'skipped'
	# - Assholes info:		'ignore', 'bad_epoch'
	# - Leveraged trading:	'net_gain'
	SIMULATOR_COLUMNS = ['bet_count', 'timestamp', 'time', 'win_bet', 'payout', 'result', 'acc', 'wacc', 'whales_bet', 'skipped', 'balance']

class StrategyParams:
	ARGS = [
		# general
		('--min_epoch', '-m', int, 0, 'min epoch'),
		('--max_epoch', '-M', int, None, 'max epoch'),
		('--max_listening_time', '-T', int, 288, 'max listening time'),
		# volume
		('--min_volume', '-v', float, 0, 'min volume'),
		('--max_volume', '-V', float,  Const.INF, 'max volume'),
		# whale detection
		('--min_whale_bet', '-wb', float, 5, 'min bet to be considered a whale'),
		('--min_whale_amount', '-w', float, None, 'min total amount of all whale bets'),
		('--max_whale_amount', '-W', float, None, 'max total whale amount'),
		# compensability (just before placing a bet, this is the min/max required amount of difference in BNB between payouts
		('--min_compensability', '-c', float, 10, 'min compensability gap'),
		('--max_compensability', '-C', float, None, 'max compensability gap'),
		('--min_anticompensability', '-ca', float, None, 'min anticompensability gap'),
		# voting
		('--min_vote_value', '-vv', float, 0, 'min value of a bet to be considered a vote'),
		('--max_vote_value', '-VV', float,  Const.INF, 'max value of a bet to be considered a vote'),
		('--min_vote_diff', '-vd', float, 10, 'min vote diff'),
		('--max_vote_diff', '-VD', float, None, 'max vote diff'),
		('--min_vote_ratio', '-vr', float, None, 'min vote ratio'),
		('--max_vote_ratio', '-VR', float, None, 'max vote ratio'),
		('--min_voting_time', '-vt', float, 0, 'min voting time'),
		('--max_voting_time', '-VT', float, Const.ROUND_DURATION, 'max voting time'),
	]
	# TODO move all the following to ARGS, make also a BOOL_ARGS
	USE_WEIGHTS = False
	COMPENSABILITY_WEIGHT = 3
	VOTE_DIFF_WEIGHT = 1
	VOTE_RATIO_WEIGHT = 5
	WEIGHT_THRESHOLD = 100
	SAVE_UPDATED_TXS = False			# False is faster, but change to True from time to time
	SAVE_UPDATED_TXS_P = 0.05			# if SAVE_UPDATED_TXS is False, this is the probability it will turn to True
	# forgiveness (only if asshole detection is activated)
	# TODO weighted forgiveness acc mode
	# TODO implement forgiveness mode based on p-value
	USE_ASSHOLE_DETECTION = True
	FORGIVENESS_MAX_ACC = 1#0.6			# maximum accuracy allowed for an asshole to be forgiven
	FORGIVENESS_MIN_COUNT = 1
	FORGIVENESS_MIN_LOSSES = 2
	FORGIVENESS_LOSSES_MODE = False
	FORGIVENESS_SUS = True
	FORGIVENESS_WEIGHTED = False
	# loss streak
	USE_LOSS_STREAK = False
	INIT_LOSS_STREAK = 2
	MAX_NET_LOSSES = 2					# maximum number of net losses allowed
	MAX_LOSS_STREAK = 3					# ignored if zero
	MAX_LOSS_STREAK_BET = 3				# ignored if zero
	LOSS_WINDOW = 10					# TODO include param for loss_window mode (not currently used)
	IGNORE_ROUNDS_DYNAMICALLY = False	# if False, it loads BAD_ROUNDS calculated by the crawler, otherwise, it does it dynamically but without forgiveness for now
	# ********************************************************************************** #
	# Please do not implement the following mode bot-side.
	# And if you do, DO NOT SET THE FOLLOWING TO TRUE WHEN USING REAL MONEY!!!
	# You would be purposefully practicing a form of insider trading, at least indirectly.
	# This is probably illegal or at least unethical!
	# And if you don't care about it, you should know that this is not a profitable strategy anyway.
	# There are many false positives in asshole detection, meaning that you would be mostly copying random players and still lose money in expected value.
	# There are many other ways to make money, and this is not one of them. This is for educational purposes only.
	# ********************************************************************************** #
	COPY_ASSHOLES = False 				# if True, asshole bets are copied
	# at -30, I usually place bets at time 279. Sometimes over 280 but just by a little. Max time is 297, so I have 18 spare seconds.
	# this also take into account the time wasted in retrieving tv predictions, so I could even have more time if I skip that
	# IMPORTANT! THIS IS 15-20 SECONDS HIGHER THAN FOCUS TIME! This also includes the time to make the API call
	# e.g. if this is 260, we need to set FOCUS_TIME to 20, if this is 265, FOCUS_TIME is 15, etc.
	MAX_LISTENING_TIME = 288			# only for simulation, for bot-side implementation there is FOCUS_TIME
	AVG_BLOCK_DURATION = 3

class Blacklist:
	BLACKLIST = []
	ROUND_VALUES = [int(x * 5) for x in range(1, 30)] + [-int(x * 5) for x in range(1, 30)]
