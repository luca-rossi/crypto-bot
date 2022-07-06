import pandas as pd
from utils.const import Const, Transactions
from utils.config import BotStrategy, StrategyParams, Blacklist

class Strategy:
	'''
	Main strategy (based on expected payout). Contains both the bot and the simulator implementation.
	'''
	params = None

	def get_params(parser):
		'''
		Get params from parser, defined in config.py.
		'''
		for (o, s, t, d, h) in StrategyParams.ARGS:
			parser.add_argument(o, s, type=t, default=d, help=h)
		# TODO in config.py, add a list of boolean args
		parser.add_argument('--opposite_vote', '-vo', action='store_true', help='the opposite vote is counted')
		return parser

	def set_params(params):
		Strategy.params = params

	def detect_assholes(df):
		'''
		Returns epochs with assholes (for the simulator).
		'''
		# TODO remove redundancy with crawler
		filter_time_tx = (df['time'] <= StrategyParams.MAX_LISTENING_TIME)
		asshole_cond_whale = df['value'].abs() >= Strategy.params.min_whale_bet
		asshole_cond_acc = None
		count_key = 'w_count' if StrategyParams.FORGIVENESS_WEIGHTED else 'count'
		acc_key = 'w_accuracy' if StrategyParams.FORGIVENESS_WEIGHTED else 'accuracy'
		cond_count = (df[count_key] < StrategyParams.FORGIVENESS_MIN_COUNT)
		cond_acc = (df[acc_key] >= StrategyParams.FORGIVENESS_MAX_ACC)
		if StrategyParams.FORGIVENESS_SUS:
			cond_asshole_round = (df['value'].round(2).abs().isin(Blacklist.ROUND_VALUES)) & (cond_count | cond_acc)
			cond_asshole_not_round = (~df['value'].round(2).abs().isin(Blacklist.ROUND_VALUES)) & ~cond_count & cond_acc
			asshole_cond_acc = cond_asshole_round | cond_asshole_not_round
		else:
			asshole_cond_acc = cond_acc
		return df[filter_time_tx & asshole_cond_whale & asshole_cond_acc].groupby('epoch').any()['value']

	def get_bot_bet(bot_params, sit_round=False, whales_tot=0, volume=0, gap=0, vote_diff=0, vote_ratio=0, remaining_time=Const.INF, loss_streak_limit=False, transaction_mode=False):
		'''
		Gets bet for the bot or returns an error message.
		'''
		# TODO if possible, try to remove the redundancy between this and the simulator method
		bet_type = None
		bullish = True
		bearish = True
		# check assholes
		# TODO PD check for assholes here directly
		if sit_round:
			return bet_type, 'Skipping: assholes detected'
		# calculate whales bets
		# TODO implement max tot too
		if bot_params.min_whale_amount is not None:
			if whales_tot > -bot_params.min_whale_amount:
				bullish = False
			if whales_tot < bot_params.min_whale_amount:
				bearish = False
			if not bullish and not bearish:
				return bet_type, 'Skipping: whales gap too low'
		# calculate gap
		if bot_params.min_compensability is not None:
			if gap < bot_params.min_compensability:
				bearish = False
			if gap > -bot_params.min_compensability:
				bullish = False
			if not bullish and not bearish:
				return bet_type, 'Skipping: compensability gap too low'
		# check vote diff
		if bot_params.min_vote_diff is not None:
			if (not bot_params.opposite_vote and vote_diff < bot_params.min_vote_diff) or (bot_params.opposite_vote and vote_diff > bot_params.min_vote_diff):
				bullish = False
			if (not bot_params.opposite_vote and vote_diff > -bot_params.min_vote_diff) or (bot_params.opposite_vote and vote_diff < -bot_params.min_vote_diff):
				bearish = False
			if not bullish and not bearish:
				return bet_type, 'Skipping: voting gap too low'
		# check vote ratio
		if bot_params.min_vote_ratio is not None:
			if vote_ratio < bot_params.min_vote_ratio:
				bullish = False
			if vote_ratio > 1 / bot_params.min_vote_ratio:
				bearish = False
			if not bullish and not bearish:
				return bet_type, 'Skipping: voting ratio too low'
		# check volume
		if volume < bot_params.min_volume:
			bullish = False
			bearish = False
			return bet_type, 'Skipping: volume too low'
		if volume > bot_params.max_volume:
			bullish = False
			bearish = False
			return bet_type, 'Skipping: volume too high'
		if not bullish and not bearish:
			return bet_type, 'Skipping: something is not right'
		# update bet type
		if (not bullish and not bearish) or (bullish and bearish):
			return bet_type, 'Skipping: no bet type'
		bet_type = Transactions.BET_BULL if bullish else Transactions.BET_BEAR
		# update remaining time again before attempting the transaction
		# check if there is a reasonable time to attempt the transaction (if it's too high or too low you risk to do it in another round)
		# it shouldn't get here, unless earlier operations in focus mode are really slow
		if remaining_time < BotStrategy.MIN_TIME_FOR_TX:
			return bet_type, 'Skipping: there isn\'t enough time to attempt the transaction'
		# check loss streak
		if loss_streak_limit:
			return bet_type, 'Skipping: too many consecutive losses'
		# check transaction mode
		if not transaction_mode:
			return bet_type, 'Skipping: transaction mode is not enabled'
		# check if, for some reason, the bot didn't choose a bet
		if bet_type is None:
			return bet_type, 'Skipping: something went wrong in choosing the bet type'
		return bet_type, None

	def get_simulator_strategy(epoch_data, epoch_inds, tf):
		'''
		Same logic of get_bot_bet() for the simulator (without asshole detection).
		'''
		filter_bullish = pd.Series().reindex_like(epoch_inds)
		filter_bullish.loc[:] = True
		filter_bearish = pd.Series().reindex_like(epoch_inds)
		filter_bearish.loc[:] = True
		# whale detection
		if Strategy.params.min_whale_amount is not None:
			filter_whales_low_bull = epoch_data['whales_bet'] < Strategy.params.min_whale_amount
			filter_whales_low_bear = epoch_data['whales_bet'] > -Strategy.params.min_whale_amount
			filter_bearish.loc[epoch_data['whales_bet'].isnull() | filter_whales_low_bull] = False
			filter_bullish.loc[epoch_data['whales_bet'].isnull() | filter_whales_low_bear] = False
		if Strategy.params.max_whale_amount is not None:
			filter_whales_high_bull = epoch_data['whales_bet'] >= Strategy.params.max_whale_amount
			filter_whales_high_bear = epoch_data['whales_bet'] <= -Strategy.params.max_whale_amount
			filter_bearish.loc[epoch_data['whales_bet'].isnull() | filter_whales_high_bull] = False
			filter_bullish.loc[epoch_data['whales_bet'].isnull() | filter_whales_high_bear] = False
		vote_diff = epoch_data['bull_votes'] - epoch_data['bear_votes']
		vote_ratio = epoch_data['bull_votes'] / epoch_data['bear_votes']
		vote_ratio.loc[vote_ratio < 1] = -1 / vote_ratio
		if StrategyParams.USE_WEIGHTS:
			bet = vote_diff * StrategyParams.VOTE_DIFF_WEIGHT + vote_ratio * StrategyParams.VOTE_RATIO_WEIGHT + epoch_data['amount_gap'] * StrategyParams.COMPENSABILITY_WEIGHT
			filter_bullish.loc[epoch_data['amount_gap'].isnull() | vote_diff.isnull() | vote_ratio.isnull() | (bet < StrategyParams.WEIGHT_THRESHOLD)] = False
			filter_bearish.loc[epoch_data['amount_gap'].isnull() | vote_diff.isnull() | vote_ratio.isnull() | (bet > -StrategyParams.WEIGHT_THRESHOLD)] = False
		else:
			if Strategy.params.min_anticompensability is not None:
				filter_gap_low_bull = (epoch_data['amount_gap'] < -Strategy.params.min_anticompensability) | (epoch_data['amount_gap'] > 0)
				filter_gap_low_bear = (epoch_data['amount_gap'] > Strategy.params.min_anticompensability) | (epoch_data['amount_gap'] < 0)
				filter_bearish.loc[epoch_data['amount_gap'].isnull() | filter_gap_low_bull] = False
				filter_bullish.loc[epoch_data['amount_gap'].isnull() | filter_gap_low_bear] = False
			else:
				if Strategy.params.min_compensability is not None:
					filter_gap_low_bull = epoch_data['amount_gap'] < Strategy.params.min_compensability
					filter_gap_low_bear = epoch_data['amount_gap'] > -Strategy.params.min_compensability
					filter_bearish.loc[epoch_data['amount_gap'].isnull() | filter_gap_low_bull] = False
					filter_bullish.loc[epoch_data['amount_gap'].isnull() | filter_gap_low_bear] = False
				if Strategy.params.max_compensability is not None:
					filter_gap_high_bull = epoch_data['amount_gap'] >= Strategy.params.max_compensability
					filter_gap_high_bear = epoch_data['amount_gap'] <= -Strategy.params.max_compensability
					filter_bearish.loc[epoch_data['amount_gap'].isnull() | filter_gap_high_bull] = False
					filter_bullish.loc[epoch_data['amount_gap'].isnull() | filter_gap_high_bear] = False
			if Strategy.params.min_vote_diff is not None:
				filter_vote_low_bull = vote_diff < Strategy.params.min_vote_diff
				filter_vote_low_bear = vote_diff > -Strategy.params.min_vote_diff
				if Strategy.params.opposite_vote:
					filter_bearish.loc[vote_diff.isnull() | filter_vote_low_bull] = False
					filter_bullish.loc[vote_diff.isnull() | filter_vote_low_bear] = False
				else:
					filter_bullish.loc[vote_diff.isnull() | filter_vote_low_bull] = False
					filter_bearish.loc[vote_diff.isnull() | filter_vote_low_bear] = False
			if Strategy.params.min_vote_ratio is not None:
				filter_vote_low_bull = vote_ratio < Strategy.params.min_vote_ratio
				filter_vote_low_bear = vote_ratio > 1 / Strategy.params.min_vote_ratio
				filter_bullish.loc[vote_ratio.isnull() | filter_vote_low_bull] = False
				filter_bearish.loc[vote_ratio.isnull() | filter_vote_low_bear] = False
			# volume
			filter_volume = (epoch_data['total_payout'] < Strategy.params.min_volume) | (epoch_data['total_payout'] > Strategy.params.max_volume)
			filter_bullish.loc[vote_ratio.isnull() | filter_volume] = False
			filter_bearish.loc[vote_ratio.isnull() | filter_volume] = False
		return filter_bullish, filter_bearish
