import pandas as pd
from modules.strategies.strategy import Strategy
from utils.config import StrategyParams, Blacklist
from utils.const import Data, IndicatorPreds, Transactions
from utils.indicators import INDICATORS

class DataProcessor:
	'''
	Processes loaded datasets and augments them to be used by the bot and the simulator.
	'''

	def get_processed_data(self, data_loader, min_epoch=None, max_epoch=None):
		'''
		Returns the processed data as two dataframes: df_epochs (which also contains data from the transactions) and df_recs (which contains data from the indicators).
		'''
		# TODO move to DataLoader
		# load epochs and transactions history
		print('Loading epochs and transactions history (it may take some time)...')
		df_epochs, df_tx = data_loader.load(min_epoch=min_epoch, max_epoch=max_epoch)
		# load tradingview predictions history
		print('Loading predictions history...')
		df_recs = data_loader.load_recs()
		# process data
		print('Augmenting txs...')
		df_tx = self.augment_txs_with_accuracy(df_tx, df_epochs, Strategy.params.min_whale_bet)
		print('Processing data...')
		df_tx = self.__process_txs(df_tx)
		df_epochs = self.__process_epochs(df_epochs, df_tx)
		df_recs = self.__process_recs(df_recs, df_epochs)
		# load indicators and strategy
		print('Loading indicators...')
		df_inds = data_loader.load_inds()
		print('Preparing strategy...')
		df_recs = self.__prepare_strategy(df_recs, df_inds, df_epochs)
		return df_epochs, df_recs

	def augment_txs_with_accuracy(self, df_tx, df_ep, min_whale_bet):
		'''
		Augments the transactions dataframe with the result and accuracy of the predictions.
		'''
		# TODO move in TxLoader, check if it still works
		# result data
		df_ep['result'] = None
		df_ep.loc[df_ep['close_price'] > df_ep['lock_price'], 'result'] = Transactions.BET_BULL
		df_ep.loc[df_ep['close_price'] < df_ep['lock_price'], 'result'] = Transactions.BET_BEAR
		df_tx = df_tx.merge(df_ep[['result']], left_on='epoch', right_index=True)
		df_tx['won'] = df_tx['input'] == df_tx['result']
		address_groups = df_tx.groupby('from')
		# accuracy data
		# shift by 1 to account for lag
		df_tx['correct'] = address_groups['won'].cumsum()
		df_tx['correct'] = address_groups['correct'].shift(1)
		df_tx['counted'] = df_tx['won'].notnull()
		df_tx['count'] = address_groups['counted'].cumsum()
		df_tx['count'] = address_groups['count'].shift(1)
		df_tx['accuracy'] = df_tx['correct'] / df_tx['count']
		df_tx['w_bets'] = False		# df_tx.loc[df_tx['value'] >= min_whale_bet, 'won']
		df_tx.loc[df_tx['value'].abs() >= min_whale_bet, 'w_bets'] = df_tx['won']
		# weighted accuracy data
		df_tx['w_correct'] = address_groups['w_bets'].cumsum()
		df_tx['w_correct'] = address_groups['w_correct'].shift(1)
		df_tx['w_counted'] = False
		df_tx.loc[df_tx['value'].abs() >= min_whale_bet, 'w_counted'] = df_tx['won'].notnull()
		df_tx['w_count'] = address_groups['w_counted'].cumsum()
		df_tx['w_count'] = address_groups['w_count'].shift(1)
		df_tx['w_accuracy'] = df_tx['w_correct'] / df_tx['w_count']
		df_tx = df_tx.drop(columns=['result', 'correct', 'counted', 'w_bets', 'w_correct', 'w_counted'])
		return df_tx

	def __process_txs(self, df):
		'''
		Processes the transactions dataframe by creating an aggregate of the transactions for each epoch.
		'''
		df['abs_value'] = df['value']
		df.loc[df['input'] == Transactions.BET_BEAR, 'value'] = -df['value']
		df['blacklisted'] = False
		df.loc[df['from'].isin(Blacklist.BLACKLIST), 'blacklisted'] = True
		filter_time_tx = (df['time'] <= StrategyParams.MAX_LISTENING_TIME)
		# TODO implement voting time bot-side too
		filter_time_voting = (df['time'] >= Strategy.params.min_voting_time) & (df['time'] <= Strategy.params.max_voting_time)
		df_grouped = pd.DataFrame()
		df_grouped['temp_bull_amount'] = df[(df['value'] > 0) & filter_time_tx].groupby('epoch').sum()['value']
		df_grouped['temp_bear_amount'] = -df[(df['value'] < 0) & filter_time_tx].groupby('epoch').sum()['value']
		df_grouped['bull_votes'] = df[(df['value'] >= Strategy.params.min_vote_value) & (df['value'] <= Strategy.params.max_vote_value) & filter_time_tx & filter_time_voting].groupby('epoch').count()['value']
		df_grouped['bear_votes'] = df[(df['value'] <= -Strategy.params.min_vote_value) & (df['value'] >= -Strategy.params.max_vote_value) & filter_time_tx & filter_time_voting].groupby('epoch').count()['value']
		df_grouped['value'] = df[(df['value'].abs() >= Strategy.params.min_whale_bet) & filter_time_tx].groupby('epoch').sum()['value']
		df_grouped['whale'] = df[(df['value'].abs() >= Strategy.params.min_whale_bet) & filter_time_tx].groupby('epoch').agg({'value': 'max', 'from': 'first'})['from']
		df_grouped['tx_bull_votes'] = df[(df['value'] <= 0.5) & (df['value'] > 0)].groupby('epoch').count()['from']
		df_grouped['tx_bear_votes'] = df[(df['value'] >= -0.5) & (df['value'] < 0)].groupby('epoch').count()['from']
		df_grouped['tx_count'] = df[filter_time_tx].groupby('epoch').count()['from']
		df_grouped['total_payout'] = df.loc[filter_time_tx].groupby('epoch').sum()['abs_value']
		if StrategyParams.USE_ASSHOLE_DETECTION:
			df_grouped['bad_epoch'] = Strategy.detect_assholes(df)
		df_grouped['ignore'] = df_grouped['bad_epoch']
		df_grouped['blacklisted'] = df[(df['blacklisted'])].groupby('epoch').any()['blacklisted']
		return df_grouped

	def __process_epochs(self, df_epochs, df_tx):
		'''
		Processes the epochs dataframe by adding transactions aggregate data and other relevant information.
		'''
		df_epochs = df_epochs.copy()
		filter_bull_win = (df_epochs['close_price'].values > df_epochs['lock_price'].values)
		filter_bear_win = (df_epochs['close_price'].values < df_epochs['lock_price'].values)
		filter_draw = (df_epochs['close_price'].values == df_epochs['lock_price'].values)
		df_epochs.loc[filter_bull_win, 'win_bet'] = Transactions.BET_BULL
		df_epochs.loc[filter_bear_win, 'win_bet'] = Transactions.BET_BEAR
		df_epochs.loc[filter_draw, 'win_bet'] = None
		df_epochs.loc[filter_bull_win, 'payout'] = 1 + df_epochs['bear_amount'] / df_epochs['bull_amount']
		df_epochs.loc[filter_bear_win, 'payout'] = 1 + df_epochs['bull_amount'] / df_epochs['bear_amount']
		df_epochs.loc[filter_draw, 'payout'] = 2
		df_epochs['tot_amount'] = df_epochs['bull_amount'] + df_epochs['bear_amount']
		# TODO arg or config param
		WINDOW_PAYOUT = 50
		# TODO optimize / remove redundancy
		df_epochs['window_payout'] = df_epochs['payout'].shift(2).rolling(WINDOW_PAYOUT).mean()
		df_epochs['temp_bull_amount'] = df_tx['temp_bull_amount']
		df_epochs['temp_bear_amount'] = df_tx['temp_bear_amount']
		df_epochs['amount_gap'] = df_epochs['temp_bull_amount'] - df_epochs['temp_bear_amount']
		df_epochs['bull_votes'] = df_tx['bull_votes']
		df_epochs['bear_votes'] = df_tx['bear_votes']
		df_epochs['whales_bet'] = df_tx['value']
		df_epochs['total_payout'] = df_tx['total_payout']
		df_epochs['tx_count'] = df_tx['tx_count']
		df_epochs['tx_bull_votes'] = df_tx['tx_bull_votes']
		df_epochs['tx_bear_votes'] = df_tx['tx_bear_votes']
		df_epochs['tx_vote_gap'] = df_epochs['tx_bull_votes'] - df_epochs['tx_bear_votes']
		df_epochs['whale'] = df_tx['whale']
		df_epochs['blacklisted'] = df_tx['blacklisted']
		df_epochs['ignore'] = df_tx['ignore']
		df_epochs['bad_epoch'] = df_tx['bad_epoch']
		if StrategyParams.COPY_ASSHOLES:
			df_epochs.loc[(df_epochs['ignore'] == False) | df_epochs['ignore'].isnull(), 'whales_bet'] = -df_epochs['whales_bet']
		else:
			df_epochs = df_epochs[(df_epochs['ignore'] == False) | df_epochs['ignore'].isnull()]
		df_epochs = df_epochs[df_epochs['blacklisted'].isnull()]
		return df_epochs

	def __process_recs(self, df_recs, df_epochs):
		'''
		Processes the recs dataframe by filling in the missing epochs (with neutral predictions).
		'''
		return df_recs.reindex(df_epochs.index).fillna(IndicatorPreds.NEUTRAL)

	def __prepare_strategy(self, df_recs, df_inds, df_epochs):
		'''
		Prepares the strategy based on technical indicators.
		'''
		df_inds = df_inds.reindex(df_epochs.index)
		df_epochs = df_epochs.copy()
		# add custom indicators
		for tf in Data.TIMEFRAMES:
			for key, value in INDICATORS.items():
				df_recs[key + '_' + tf] = value(df_epochs, df_inds, tf)
		# augment indicators
		# TODO generalize "augmentation options"
		inds = list(df_recs.columns)
		for ind in inds:
			rev = 'rev_' + ind
			ignore_bs = 'ignore_bs_' + ind
			ignore_n = 'ignore_n_' + ind
			filter_buy = df_recs[ind] == IndicatorPreds.BET_BULL
			filter_sell = df_recs[ind] == IndicatorPreds.BET_BEAR
			filter_neutral = df_recs[ind] == IndicatorPreds.NEUTRAL
			df_recs.loc[filter_buy, rev] = IndicatorPreds.BET_BEAR
			df_recs.loc[filter_buy, ignore_bs] = IndicatorPreds.IGNORE
			df_recs.loc[filter_buy, ignore_n] = IndicatorPreds.OKAY
			df_recs.loc[filter_sell, rev] = IndicatorPreds.BET_BULL
			df_recs.loc[filter_sell, ignore_bs] = IndicatorPreds.IGNORE
			df_recs.loc[filter_sell, ignore_n] = IndicatorPreds.OKAY
			df_recs.loc[filter_neutral, rev] = IndicatorPreds.NEUTRAL
			df_recs.loc[filter_neutral, ignore_bs] = IndicatorPreds.OKAY
			df_recs.loc[filter_neutral, ignore_n] = IndicatorPreds.IGNORE
		# return a copy to defragment the df
		return df_recs.copy()

	def normalize_inds(self, df_recs, df_inds, df_epochs):
		'''
		Normalizes the indicators (particularly useful for strategies based on machine learning).
		'''
		# TODO not currently used, but could be useful to generalize normalization. This commented part is from old code, adapt it to dataframes
		# for ind in IndicatorAnalysis.ANALYSIS_IND:
		# 	if ind in IndicatorAnalysis.ANALYSIS_IND_NORM_PRICE:
		# 		# value /= (1000 * lock_price)
		# 		value = 100 * (1 - (value / (1000 * lock_price)))
		# 		diff_temp[ind + '_' + tf] = value
		# 	else:
		# 		if ind in IndicatorAnalysis.ANALYSIS_IND_NORM_100:
		# 			value /= 100
		# 		value = round(value, 2)
		# for i, (ind, value) in enumerate(diff_temp.items()):
		# 	for i2, (ind2, value2) in enumerate(diff_temp.items()):
		# 		if i2 <= i:
		# 			continue
		# 		temp_tree[ind + ind2] = value - value2
		# payout = bear_amount / bull_amount if result == 1 else bull_amount / bear_amount
		# value = 1 if payout > 1 else 0
		return
