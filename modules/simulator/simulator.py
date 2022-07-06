import numpy as np
import pandas as pd
from datetime import datetime
from modules.strategies.window import Window
from utils.config import SimulatorSettings, StrategyParams
from utils.const import SimLogOptions, Transactions, IndicatorPreds
from utils.utils import Utils

class Simulator:
	'''
	Simulates a strategy on historical data. The bot-side 2-epoch lag has to be considered by the simulator:
	-1 is the epoch to guess, we need to bet on this one (payouts are updating).
	-2 is the current epoch, happening right now (payouts updated but no close price yet).
	-3 is the latest one with payout info.
	'''
	# TODO test if whale detection still matches between the simulator and the bot (it should work)
	window = None
	window_data = None

	def __init__(self, window_data):
		'''
		Initializes the simulator with the window.
		'''
		self.window_data = window_data
		self.window = Window(window_data)

	def simulate(self, ind_names, ind_values=None, epochs_data=None, attempts=None, calculate_pvalue=False, window_data=None, min_tot=0, log_options=[]):
		'''
		Simulates the strategy given by ind_names and ind_values on historical data given by epochs_data.
		'''
		# TODO min_tot: check that at least N bets have been made
		# init window
		window_data = self.__init_window(window_data)
		# copy the df so we can work on data (e.g. edit payout)
		df_epochs = epochs_data.copy()
		# get reindexed inds df
		df_inds = self.__get_df_inds(df_epochs, ind_names, ind_values)
		# get the price change from last day (for statistical / strategic purposes)
		df_epochs['change_perc'] = self.__get_change_perc(df_epochs)
		# count rounds and get simulated time
		if SimLogOptions.EPOCHS in log_options:
			df_epochs['timestamp'] = self.__get_timestamp(df_epochs)
			df_epochs['time'] = self.__get_time(df_epochs)
		# check if the epoch is bettable (with indicators and a valid payout) and if the transaction is attempted
		filter_bettable = self.__get_filter_bettable(df_epochs)
		# get prediction from inds
		df_epochs['pred'] = self.__get_pred(df_epochs, df_inds, filter_bettable)
		# calculate variance window
		df_epochs['var_window'] = self.__get_var_window(df_epochs, window_data)
		# calculate window accuracies
		df_epochs['avg_payout_acc'] = self.__get_avg_payout_acc(df_epochs, window_data)
		df_epochs['avg_window_acc'] = self.__get_avg_window_acc(df_epochs, window_data)
		# get the final bet, which is not necessarily the same as the prediction
		df_epochs['bet'] = self.__get_bet(df_epochs, window_data, filter_bettable)
		# increment total payout with new bet
		df_epochs['bull_amount'] = self.__get_updated_amount(df_epochs, Transactions.BET_BULL)
		df_epochs['bear_amount'] = self.__get_updated_amount(df_epochs, Transactions.BET_BEAR)
		df_epochs['payout'] = self.__get_updated_payout(df_epochs)
		# get result and bet count
		filter_win, filter_lose = self.__get_result_filters(df_epochs)
		df_epochs['result'] = self.__get_result(df_epochs, filter_win, filter_lose)
		df_epochs['bet_count'] = self.__get_bet_count(df_epochs)
		# get loss streak
		df_epochs['loss_streak'], df_epochs['loss_window'] = self.__get_loss_streak_with_window(df_epochs)
		filter_loss_streak = self.__get_loss_streak_filter(df_epochs)
		# update balance
		df_epochs['balance'] = self.__get_updated_balance(df_epochs, filter_win, filter_lose, filter_loss_streak)
		# TODO include leveraged trading info: the wisdom of the crowd could be used for leveraged trading (early results are not promising)
		# # get price difference (not enough, it could be liquidated before getting there, but it's unlikely)
		# df_epochs['net_gain'] = self.__get_net_gain(df_epochs)
		# # from here, get pred
		# trading result = trade size * (price diff / lock price - fee)
		# df_epochs['trading_balance'] = self.__get_net_gain(df_epochs)
		# TODO implement Kelly criterion (capped at 1 BNB) and/or dynamic bet proportional to the estimated volume (based on a moving average)
		# # get balance with Kelly mode (commented until implemented)
		# df_epochs['kelly_balance'] = self.__get_kelly_balance(df_epochs)
		# calculate max loss
		# TODO vectorize if possible
		max_loss = 0
		max_balance = 0
		for i, epoch in df_epochs.iterrows():
			balance = epoch['balance']
			max_balance = max(balance, max_balance)
			loss = max_balance - balance
			max_loss = max(loss, max_loss)
		# check skipped rounds
		df_epochs['skipped'] = ~filter_loss_streak
		# calculate accuracy values
		filter_correct = filter_win.reindex_like(df_epochs)
		df_epochs['correct'] = filter_correct.cumsum()
		df_epochs['w_correct'] = (filter_correct * (df_epochs['payout'] - 1)).cumsum()
		df_epochs['acc'] = df_epochs['correct'] / df_epochs['bet_count']
		df_epochs['wacc'] = df_epochs['w_correct'] / df_epochs['bet_count']
		# TODO get balance volatility (std) - Vectorize
		# std = self.__get_balance_std(balance_history, max_balance, tot)
		# TODO get payout volatility (std) - Move in DataProcessor?
		# PAYOUT_VAR_WINDOW = 100
		# df_epochs['payout_var'] = 100 * df_epochs['payout'].shift(2).rolling(PAYOUT_VAR_WINDOW).std()# / df_epochs['payout'].shift(2).rolling(PAYOUT_VAR_WINDOW).mean()
		# TODO remove log_options?
		if SimLogOptions.EPOCHS in log_options:
			rows = df_epochs['pred'].notnull()
			mean_payout = df_epochs.loc[df_epochs['result'] == 'W', 'payout'].mean()
			median_payout = df_epochs.loc[df_epochs['result'] == 'W', 'payout'].median()
			mean_ev = df_epochs.iloc[-1]['acc'] * (mean_payout - 1) - (1 - df_epochs.iloc[-1]['acc'])
			median_ev = df_epochs.iloc[-1]['acc'] * (median_payout - 1) - (1 - df_epochs.iloc[-1]['acc'])
			# the Kelly formula (edge/odds), in expanded form, is: (P*W-L)/P
			# in this formula, P is the payoff, W is the probability of winning, and L is the probability of losing) / P
			mean_kelly = ((mean_payout - 1) * df_epochs.iloc[-1]['acc'] - (1 - df_epochs.iloc[-1]['acc'])) / (mean_payout - 1)
			median_kelly = ((median_payout - 1) * df_epochs.iloc[-1]['acc'] - (1 - df_epochs.iloc[-1]['acc'])) / (median_payout - 1)
			print(df_epochs.loc[rows, SimulatorSettings.SIMULATOR_COLUMNS].to_string())			# print all results
			print(df_epochs.loc[1::280, SimulatorSettings.SIMULATOR_COLUMNS].to_string())		# print daily results
			print(df_epochs.loc[1::1960, SimulatorSettings.SIMULATOR_COLUMNS].to_string())		# print monthly results
			print('Mean payout: ' + str(mean_payout))
			print('Median payout: ' + str(median_payout))
			print('Max loss: ' + str(max_loss))
			print('Round expected profit (mean): ' + str(mean_ev))
			print('Round expected profit (median): ' + str(median_ev))
			print('Kelly (mean): ' + str(mean_kelly))
			print('Kelly (median): ' + str(median_kelly))
		# columns = ['balance']
		# result = df_epochs.iloc[-1].to_dict()
		# result = dict((k, result[k]) for k in columns if k in result)
		# accuracy = correct / tot
		# weighted_accuracy = weighted_correct / tot
		# TODO test this
		# std = self.__get_balance_std(balance_history, max_balance, tot)
		# p_value_acc = binom.sf(k=correct, n=tot, p=0.5) + binom.pmf(k=correct, n=tot, p=0.5) if calculate_pvalue else 0
		# p_value_wacc = binom.sf(k=int(weighted_correct), n=tot, p=0.5) + binom.pmf(k=int(weighted_correct), n=tot, p=0.5) if calculate_pvalue else 0
		# att = attempts or len(ind_values)**len(inds) if calculate_pvalue else 0
		# p_value_acc_ind = binom.sf(k=1, n=att, p=p_value_acc) + binom.pmf(k=1, n=att, p=p_value_acc) if calculate_pvalue else 0
		# p_value_wacc_ind = binom.sf(k=1, n=att, p=p_value_wacc) + binom.pmf(k=1, n=att, p=p_value_wacc) if calculate_pvalue else 0
		result = {
			'inds': ind_names,
			'last_epoch': df_epochs.index[-1],
			'rounds': df_epochs.iloc[-1]['bet_count'],
			'tot': df_epochs[filter_bettable].shape[0],
			'acc': round(df_epochs.iloc[-1]['acc'], 2),
			'wacc': round(df_epochs.iloc[-1]['wacc'], 2),
			# 'std': round(std, 2),
			# 'p_value_acc': p_value_acc,
			# 'p_value_acc_ind': p_value_acc_ind,
			# 'p_value_wacc': p_value_wacc,
			# 'p_value_wacc_ind': p_value_wacc_ind,
			'balance': round(df_epochs.iloc[-1]['balance'], 2)
		}
		# TODO when searching, build df with solutions and print
		# print()
		# print(result)
		# if SimLogOptions.SAVE_WINDOW in log_options:
		# 	# save averages to bot_window
		# 	f = open(Files.LOG_WINDOW, 'w')
		# 	f.write(str(known_epoch) + '\n')
		# 	f.write(str(avg_payout_accuracy) + '\n')
		# 	f.write(str(avg_window_accuracy) + '\n')
		# 	f.close()
		# if SimLogOptions.CSV in log_options:
		# 	df_results.to_csv('experiments/' + str(datetime.now().strftime("%Y%m%d%H%M")) + '.csv')
		return result

	def __init_window(self, window_data):
		window_data = window_data or self.window_data or SimulatorSettings.DEFAULT_WINDOW_DATA
		self.window.set_window_data(window_data)
		return window_data

	def __get_change_perc(self, df_epochs):
		series_prev_price = df_epochs['close_price'].shift(periods=288, fill_value=0)
		return 100 * (df_epochs['close_price'] / series_prev_price - 1)

	def __get_timestamp(self, df_epochs):
		return df_epochs.apply(lambda x: datetime.fromtimestamp(x['end_time']), axis=1)

	def __get_time(self, df_epochs):
		series_count = df_epochs['start_time'].notnull().cumsum()
		return series_count.apply(lambda x: Utils.get_time_from_count(x))

	def __get_df_inds(self, df_epochs, ind_names, ind_values):
		df_inds = ind_values.loc[:, list(set(ind_names))]
		return df_inds.reindex(df_epochs.index, fill_value=False)

	def __get_filter_bettable(self, df_epochs):
		return (df_epochs['lock_price'] > 0) & (df_epochs['close_price'] > 0) & (df_epochs['bull_amount'] > 0) & (df_epochs['bear_amount'] > 0)

	def __get_pred(self, df_epochs, df_inds, filter_bettable):
		pred = pd.Series().reindex_like(df_epochs)
		filter_bet_bull = filter_bettable.copy()
		filter_bet_bear = filter_bettable.copy()
		# get prediction and increment total payout
		for ind in df_inds:
			filter_ignore = df_inds[ind].values == IndicatorPreds.IGNORE
			filter_buy = (df_inds[ind].values != IndicatorPreds.IGNORE.OKAY) & (df_inds[ind].values != IndicatorPreds.BET_BULL)
			filter_sell = (df_inds[ind].values != IndicatorPreds.IGNORE.OKAY) & (df_inds[ind].values != IndicatorPreds.BET_BEAR)
			filter_bet_bull.loc[filter_ignore | filter_buy] = False
			filter_bet_bear.loc[filter_ignore | filter_sell] = False
		pred.loc[:] = None
		pred.loc[filter_bet_bull.values] = Transactions.BET_BULL
		pred.loc[filter_bet_bear.values] = Transactions.BET_BEAR
		pred.loc[filter_bet_bull.values & filter_bet_bear.values] = None
		# -1 shift because of the lag
		return pred.shift(-1)

	def __get_var_window(self, df_epochs, window_data):
		# df_epochs['var_window'] = 100 * df_epochs['close_price'].shift(2).rolling(window_data['var_window']).std() / df_epochs['close_price'].shift(2).rolling(window_data['var_window']).mean()
		return (df_epochs['close_price'] - df_epochs['lock_price']).abs().shift(2).rolling(window_data['var_window']).median() / 100

	def __get_avg_payout_acc(self, df_epochs, window_data):
		filter_payout_win = ((df_epochs['payout'] > 0) & (df_epochs['payout'] < 2)).shift(2, fill_value=False)
		known_payout_win = pd.Series().reindex_like(df_epochs)
		known_payout_win.loc[filter_payout_win] = 1
		known_payout_win.loc[~filter_payout_win] = 0
		return known_payout_win.ewm(span=window_data['payout_window']).mean()

	def __get_avg_window_acc(self, df_epochs, window_data):
		filter_pred_win = df_epochs['pred'].notnull() & (df_epochs['pred'] == df_epochs['win_bet'])
		filter_pred_lose = df_epochs['pred'].notnull() & (df_epochs['pred'] != df_epochs['win_bet'])
		filter_pred_sit = df_epochs['pred'].isnull()
		df_epochs.loc[filter_pred_win, 'my_win'] = 1 + window_data['bet_win_window_weight']
		df_epochs.loc[filter_pred_lose, 'my_win'] = - window_data['bet_loss_window_weight']
		df_epochs.loc[filter_pred_sit, 'my_win'] = 0.5
		known_my_win = pd.Series().reindex_like(df_epochs)
		known_my_win = df_epochs['my_win'].shift(2, fill_value=0.5)
		return known_my_win.ewm(span=window_data['my_window']).mean()

	def __get_bet(self, df_epochs, window_data, filter_bettable):
		bet = pd.Series().reindex_like(df_epochs)
		filter_var_window = (df_epochs['var_window'] < window_data['max_var'])
		filter_payout_window = (df_epochs['avg_payout_acc'] > window_data['min_payout_accuracy'])
		filter_my_window = (df_epochs['avg_window_acc'] > window_data['min_window_accuracy'])
		filter_outliers = (df_epochs['payout'] < SimulatorSettings.MAX_PAYOUT)
		# TODO filter window losses
		filter_attempted = filter_bettable & filter_outliers & filter_payout_window & filter_my_window & filter_var_window
		bet.loc[:] = None
		bet.loc[filter_attempted] = df_epochs['pred']
		return bet

	def __get_updated_amount(self, df_epochs, transaction_type):
		amount = df_epochs['bull_amount'].copy() if transaction_type == Transactions.BET_BULL else df_epochs['bear_amount'].copy()
		filter = (df_epochs['payout'].notnull()) & (df_epochs['bet'] == transaction_type)
		amount[filter] += SimulatorSettings.BET_AMOUNT
		return amount

	def __get_updated_payout(self, df_epochs):
		# TODO optimize: copied from DataProcessor, payout calculated twice
		payout = pd.Series().reindex_like(df_epochs)
		filter_bull_win = (df_epochs['close_price'].values > df_epochs['lock_price'].values)
		filter_bear_win = (df_epochs['close_price'].values < df_epochs['lock_price'].values)
		payout.loc[:] = 0
		payout.loc[filter_bull_win] = 1 + df_epochs['bear_amount'] / df_epochs['bull_amount']
		payout.loc[filter_bear_win] = 1 + df_epochs['bull_amount'] / df_epochs['bear_amount']
		return payout

	def __get_result_filters(self, df_epochs):
		filter_win = df_epochs['bet'].notnull() & (df_epochs['bet'] == df_epochs['win_bet'])
		filter_lose = df_epochs['bet'].notnull() & (df_epochs['bet'] != df_epochs['win_bet'])
		return filter_win, filter_lose

	def __get_result(self, df_epochs, filter_win, filter_lose):
		result = pd.Series().reindex_like(df_epochs)
		result.loc[filter_win] = 'W'
		result.loc[filter_lose] = 'L'
		return result

	def __get_bet_count(self, df_epochs):
		return df_epochs['bet'].notnull().cumsum()

	def __get_loss_streak_with_window(self, df_epochs):
		loss_streak = pd.Series().reindex_like(df_epochs).fillna(0)
		loss_window = pd.Series().reindex_like(df_epochs).fillna(0)
		# TODO replace with exp moving average
		losses = [0] * StrategyParams.LOSS_WINDOW
		if StrategyParams.USE_LOSS_STREAK:
			streak = 0
			j = 0
			# TODO vectorize if possible
			# loss_streak_prev = losses.shift(1)
			# loss_streak = losses + loss_streak_prev
			# loss_streak = loss_streak.rolling(2).cumsum()
			# loss_streak = df_epochs.apply(lambda x: x['loss_streak'].shift(1) + (x['result'] == 'L'), axis=1)
			for i, epoch in df_epochs.iterrows():
				if epoch['result'] == 'L':
					streak += 1
					j += 1
				elif epoch['result'] == 'W':
					streak -= 1
					j += 1
				if streak < 0:
					streak = 0
				if streak > StrategyParams.MAX_LOSS_STREAK:
					streak = StrategyParams.MAX_LOSS_STREAK
				losses[j % len(losses)] = streak
				loss_streak.loc[i] = streak
				loss_window.loc[i] = sum(losses) / len(losses)
		loss_streak = loss_streak.shift(1)
		loss_window = loss_window.shift(1)
		return loss_streak, loss_window

	def __get_loss_streak_filter(self, df_epochs):
		return df_epochs['bet'].notnull() & (df_epochs['loss_streak'] < StrategyParams.MAX_LOSS_STREAK_BET)

	def __get_updated_balance(self, df_epochs, filter_win, filter_lose, filter_loss_streak=True):
		balance = pd.Series().reindex_like(df_epochs).fillna(0)
		fee_abs_win = SimulatorSettings.FEE_ABS_BSC_CLAIM + SimulatorSettings.FEE_ABS_BSC
		fee_rel = 1 - SimulatorSettings.FEE_REL_PS
		balance.loc[filter_win & filter_loss_streak] = SimulatorSettings.BET_AMOUNT * (df_epochs.loc[filter_win, 'payout'] * fee_rel - 1) - fee_abs_win
		balance.loc[filter_lose & filter_loss_streak] = - SimulatorSettings.BET_AMOUNT - SimulatorSettings.FEE_ABS_BSC
		balance = balance.cumsum() + SimulatorSettings.INIT_BALANCE
		return balance

	def __get_net_gain(self, df_epochs):
		return (df_epochs['close_price'] - df_epochs['lock_price']) / df_epochs['lock_price'] - SimulatorSettings.FEE_TRADING

	def  __get_kelly_balance(df_epochs):
		# TODO implement kelly mode, vectorize if possible
		# balance = 200
		# kelly = 0.1
		# for i, epoch in df_epochs.iterrows():
		# 	bet_amount = balance * kelly
		#	# do stuff...
		return

	def __get_trading_balance(self, df_epochs, filter_win, filter_lose, filter_loss_streak=True):
		# TODO complete this (leveraged trading simulator)
		balance = pd.Series().reindex_like(df_epochs).fillna(0)
		fee_abs_win = SimulatorSettings.FEE_ABS_BSC_CLAIM + SimulatorSettings.FEE_ABS_BSC
		fee_rel = 1 - SimulatorSettings.FEE_REL_PS
		balance.loc[filter_win & filter_loss_streak] = SimulatorSettings.BET_AMOUNT * (df_epochs.loc[filter_win, 'payout'] * fee_rel - 1) - fee_abs_win
		balance.loc[filter_lose & filter_loss_streak] = - SimulatorSettings.BET_AMOUNT - SimulatorSettings.FEE_ABS_BSC
		balance = balance.cumsum() + SimulatorSettings.INIT_BALANCE
		return balance

	def __get_balance_std(self, balance_history, balance, tot):
		if tot == 0:
			return 0
		avg_epoch_gain = (balance - SimulatorSettings.INIT_BALANCE) / tot
		errors = []
		for i in range(len(balance_history)):
			avg_b = SimulatorSettings.INIT_BALANCE + (i + 1) * avg_epoch_gain
			error = (balance_history[i] - avg_b)# / avg_b
			errors.append(error)
		std = np.std(errors)
		return 0 if np.isnan(std) else std
