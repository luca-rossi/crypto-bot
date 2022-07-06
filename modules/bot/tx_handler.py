from modules.data import DataLoader
from modules.strategies.strategy import Strategy
from utils.config import Blacklist, StrategyParams
from utils.const import ContractMethods, Transactions
from utils.utils import Utils

class TxHandler:
	'''
	Handles the datasets used by the bot, specifically the epochs and the transactions.
	'''
	contract = None
	data_loader = None
	df_epochs = None
	df_tx = None

	def __init__(self, contract):
		self.contract = contract
		self.data_loader = DataLoader()

	def load(self):
		'''
		Loads the datasets used by the bot (epochs and transactions). This is done once at the beginning of the bot's execution and at every new round (if specified) to get the latest data.
		'''
		self.df_epochs, self.df_tx = self.data_loader.load()

	def loaded(self):
		'''
		Checks if the datasets have been loaded at least once.
		'''
		return self.df_epochs is not None and self.df_tx is not None

	def detect_txs(self, round_data, bot_params, start_time=0, all_from_round=False):
		'''
		Detects the latest transactions by other users. Checks if these transactions are valid and check if they are made from whales/assholes.
		'''
		assholes_detected = False
		log = ''
		txs = self.contract.retrieve_round_txs() if all_from_round else self.contract.retrieve_new_txs()
		for tx in txs:
			value, bullish, bearish = None, None, None
			address = str(tx['from']).lower()
			# check if the whale hasn't been found yet
			is_valid_tx = all_from_round or address not in round_data.whales
			if is_valid_tx:
				value = round(Utils.normalize_amount(int(tx['value'])), 4)
				bullish = ContractMethods.BULL_METHOD in tx['input']
				bearish = ContractMethods.BEAR_METHOD in tx['input']
			# if the new tx is a whale, increment the number of found txs
			is_valid_tx = is_valid_tx and int(tx['timeStamp']) >= start_time and (bullish or bearish)
			if is_valid_tx:
				round_data.add_tx_vote(address, value, bullish)
				round_data.tx_log += '\n' + str(address) + ' - ' + str(int(tx['timeStamp']) - start_time)
			else:
				round_data.tx_log += '.'
			# check if the whale is bullish or bearish and add to whales dict (it's unnecessary to check twice, but do it just in case)
			is_valid_tx = is_valid_tx and value >= bot_params.min_whale_bet
			if is_valid_tx:
				if bullish:
					round_data.whales[address] = value
				if bearish:		# check is unnecessary but do it anyway
					round_data.whales[address] = -value
				# check if the whale is an asshole
				count, correct = self.__get_address_accuracy(address, weighted=True)
				accuracy = correct / count
				cond_asshole_round = value in Blacklist.ROUND_VALUES and (count < StrategyParams.FORGIVENESS_MIN_COUNT or accuracy >= StrategyParams.FORGIVENESS_MAX_ACC)
				cond_asshole_not_round = value not in Blacklist.ROUND_VALUES and (count >= StrategyParams.FORGIVENESS_MIN_COUNT and accuracy >= StrategyParams.FORGIVENESS_MAX_ACC)
				if StrategyParams.USE_ASSHOLE_DETECTION and (cond_asshole_round or cond_asshole_not_round):
					assholes_detected = True
					log += '\nAsshole detected! ' + str(address) + ' - ' + str(value) + ' BNB - Count ' + str(count) + ' - Accuracy ' + str(accuracy)
				else:
					log += '\nNormal whale detected! ' + str(address) + ' - ' + str(value) + ' BNB - Count ' + str(count) + ' - Accuracy ' + str(accuracy)
		return assholes_detected, log

	def __get_address_accuracy(self, address, weighted=False):
		'''
		Calculates the accuracy of the given address.
		'''
		# TODO consider moving to DataProcessor (merge with augment_txs_with_accuracy?), include weighted accuracy
		df_whale_txs = self.df_tx[self.df_tx['from'] == address]
		df_whale_txs.loc[df_whale_txs['input'] == Transactions.BET_BEAR, 'value'] = -df_whale_txs['value']
		df_whale_txs = df_whale_txs.merge(self.df_epochs, on='epoch', how='left')
		df_whale_txs['result'] = None
		df_whale_txs.loc[df_whale_txs['close_price'] > df_whale_txs['lock_price'], 'result'] = Transactions.BET_BULL
		df_whale_txs.loc[df_whale_txs['close_price'] < df_whale_txs['lock_price'], 'result'] = Transactions.BET_BEAR
		correct = (df_whale_txs['input'] == df_whale_txs['result']).sum()
		count = df_whale_txs.shape[0]
		# if weighted:
		# 	return df_whale_txs['w_count'][-1], df_whale_txs['w_correct'][-1]
		# return df_whale_txs['count'][-1], df_whale_txs['correct'][-1]
		return count, correct
