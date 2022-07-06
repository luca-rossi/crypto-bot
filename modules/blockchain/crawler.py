import pandas as pd
from modules.blockchain.contract import Contract
from utils.config import Files, StrategyParams, Blacklist
from utils.const import Transactions


class Crawler():
	'''
	Includes all the methods related to blockchain crawling, it reads and processes the transactions on the contract.
	In particulr, it crawls the blockchain to build the blacklist (asshole detectioin).
	'''
	contract = None
	df_ep = None
	df_tx = None

	def __init__(self, contract=None):
		'''
		Loads the contract and the datasets.
		'''
		# TODO consider calling the relevant methods to load the datasets
		self.contract = contract if contract else Contract()
		self.df_ep = pd.read_csv(Files.LOG_EPOCHS)
		self.df_tx = pd.read_csv(Files.LOG_TXS)

	def expand_blacklist_graph(self, blacklist, verbose=False, max_timestamp=None):
		'''
		Gets a blacklist as input and returns another blacklist obtained by expanding the graph by one level.
		Only "normal" transfers are considered (transfers to smart contracts are excluded).
		'''
		if verbose:
			print(blacklist)
		new_blacklist = blacklist.copy()
		for address in blacklist:
			if verbose:
				print(address)
			txs = self.contract.get_address_txs(address)
			if txs is not None and len(txs) > 0:
				for a in txs:
					if a['input'] == '0x' and (max_timestamp is None or int(a['timeStamp']) <= int(max_timestamp)):
						if a['from'] == address:
							new_blacklist.add(a['to'])
						else:
							new_blacklist.add(a['from'])
		return new_blacklist

	def save_address_info(self):
		'''
		Saves to file relevant info about addresses (e.g. accuracy).
		'''
		# TODO implement (veectorized), currently not used
		return

	def simulate_realtime_blacklist(self, min_epoch, max_epoch, min_bet, min_accuracy, min_count, round_forgiveness,
									strategy_rounds, strategy_acc, strategy_sus, strategy_graph, strategy_whitelist,
									log_every, verbose):
		'''
		Simulates epochs to show how the blacklist would have been built in real-time rather than in hindsight (when we already know who are the assholes).
		Epochs are iterated (not vectorized) to simulate real-time operations. Whales are added to the blacklist incrementally.
		Used to test different blacklist creation strategies.
		'''
		# TODO default params
		# TODO this is a long method (also, probably buggy), refactor it by splitting it into smaller private methods
		# TODO "epoch" here is the current epoch, not the epoch to predict! Refactor "epoch" everywhere, distinguish between curr_epoch and pred_epoch
		# TODO refactor addresses as a df, include saving option
		addresses = {}			# address: {count, accuracy, blacklisted}
		rounds_to_ignore = []
		blacklist = set()		# build blacklist with VERY STRICT CRITERIA because this will be used for graph expansion
		graylist = set()		# the graylist has less strict criteria, addresses will still be ignored but not used for graph expansion
		for epoch, epoch_data in self.df_ep.iterrows():
			if epoch < min_epoch:
				continue
			if epoch > max_epoch:
				break
			# addresses added to the graylist at the end of this epoch
			epoch_graylist = set()
			# TODO this should already be in df_ep if we load the augmented one
			winning_bet = Transactions.BET_BULL if epoch_data['close_price'] > epoch_data['lock_price'] else (Transactions.BET_BEAR if epoch_data['close_price'] < epoch_data['lock_price'] else None)
			whales = self.df_tx[(self.df_tx['epoch'] == epoch) & (self.df_tx['value'] >= min_bet)]
			# TODO inculude MAX_LISTENING_TIME
			# loop through detected whales: this could be vectorized but it's unnecessary since there are max 1-2 whales each epoch
			if len(whales) > 0:
				for _, whale in whales.iterrows():
					address = whale['from']
					time = whale['time']
					correct = whale['input'] == winning_bet
					is_round = whale['value'] in Blacklist.ROUND_VALUES if len(Blacklist.ROUND_VALUES) > 0 else True
					if verbose:
						print(epoch)
						print(address)
						print(whale['input'])
						print(whale['value'])
						print(round(whale['value'], 2))
						print(round(whale['value'], 2) in Blacklist.ROUND_VALUES)
						print(whale['value'] in Blacklist.ROUND_VALUES)
						print(round(whale['value'], 2) in Blacklist.ROUND_VALUES)
						print()
					# don't save expanded graph, just check to ignore the round, then add the address to the blacklist according to criteria
					if strategy_graph:
						# if the address is already blacklisted, we graylist it in this round
						if address in blacklist:
							epoch_graylist.add(address)
						elif len(blacklist) > 0:
							# TODO dynamically expand graph to a leved passed as an argument
							graph = self.expand_blacklist_graph({address}, max_timestamp=whale['timeStamp'])		# level 1
							graph = self.expand_blacklist_graph(graph, max_timestamp=whale['timeStamp'])			# level 2
							if len(blacklist & graph) > 0:
								print('Graph criteria met')
								print(graph)
								print(blacklist & graph)
								blacklist.add(address)
								epoch_graylist.add(address)
								print(blacklist)
					# graylist according to rounds strategy
					if strategy_rounds and is_round:
						if time <= StrategyParams.MAX_LISTENING_TIME:
							# TODO make an arg
							if round_forgiveness:
								forgiveness_cond = address in addresses
								if StrategyParams.FORGIVENESS_LOSSES_MODE:
									# TODO temp solution, replace with and test the commented out code
									# forgiveness_cond = forgiveness_cond and addresses[address]['count'] - addresses[address]['correct'] >= StrategyParams.FORGIVENESS_MIN_LOSSES
									forgiveness_cond = forgiveness_cond and is_round and addresses[address]['accuracy'] < min_accuracy
								else:
									forgiveness_cond = forgiveness_cond and is_round and addresses[address]['count'] >= min_count and addresses[address]['accuracy'] < min_accuracy
								if not forgiveness_cond:
									epoch_graylist.add(address)
							else:
								epoch_graylist.add(address)
					# graylist according to accuracy / whitelist strategy
					if address in addresses:
						if strategy_acc and addresses[address]['accuracy'] >= min_accuracy:
							epoch_graylist.add(address)
						if strategy_whitelist and (addresses[address]['count'] < min_count or addresses[address]['accuracy'] >= min_accuracy):
							epoch_graylist.add(address)
						addresses[address]['count'] += 1
						addresses[address]['correct'] += 1 if correct else 0
						addresses[address]['round_count'] += 1 if is_round else 0
						addresses[address]['roundness'] = round(addresses[address]['round_count'] / addresses[address]['count'], 4)
						addresses[address]['accuracy'] = round(addresses[address]['correct'] / addresses[address]['count'], 4)
						addresses[address]['w_count'] += round(whale['value'], 4)
						addresses[address]['w_correct'] += round(whale['value'] if correct else 0, 4)
						addresses[address]['w_accuracy'] = round(addresses[address]['w_correct'] / addresses[address]['w_count'], 4)
						addresses[address]['last_epoch'] = epoch
					else:
						addresses[address] = {
							'count': 1,
							'correct': 1 if correct else 0,
							'round_count': 1 if is_round else 0,
							'roundness': 1 if is_round else 0,
							'accuracy': 1 if correct else 0,
							'w_count': round(whale['value'], 4),
							'w_correct': round(whale['value'] if correct else 0, 4),
							'w_accuracy': 1 if correct else 0,
							'last_epoch': epoch,
						}
						if strategy_sus or strategy_whitelist:
							epoch_graylist.add(address)
					# when the round is finished, check blacklist criteria (VERY STRICT, avoid false positives since a graph will be expanded from this)
					# criteria are less strict if we just update the blacklist (graph) every round with forgiveness
					# if strategy_graph and addresses[address]['count'] >= 4 and int(addresses[address]['accuracy']) == 1 and int(addresses[address]['roundness']) == 1:
					if strategy_graph and addresses[address]['count'] >= 3 and int(addresses[address]['accuracy']) == 1:
						print('Blacklist criteria met')
						blacklist.add(address)
						print(address)
			if epoch % log_every == 0:
				df_addresses = pd.DataFrame.from_dict(addresses, orient='index')
				# TODO file as arg or config param
				df_addresses.to_csv('logs/addresses_full_new.csv')
				self.__show_blacklist_log(epoch, addresses, rounds_to_ignore, blacklist, graylist)
			for address in epoch_graylist:
				graylist.add(address)
			if len(epoch_graylist) > 0:
				rounds_to_ignore.append(epoch)
		df_addresses = pd.DataFrame.from_dict(addresses, orient='index')
		df_addresses.to_csv('logs/addresses_full_new.csv')
		self.__show_blacklist_log(epoch, addresses, rounds_to_ignore, blacklist, graylist)

	def __show_blacklist_log(self, epoch, addresses, rounds_to_ignore, blacklist, graylist):
		'''
		Visualizes blacklist info.
		'''
		print(epoch)
		if addresses:
			df = pd.DataFrame.from_dict(addresses, orient='index')
			df['graylisted'] = df.index.isin(graylist)
			df['blacklisted'] = df.index.isin(blacklist)
			print(df.to_string())
		# for k, v in addresses.items():
		# 	print(k + ' - ' + str(v))
		print()
		rounds_to_ignore = list(set(rounds_to_ignore))
		rounds_to_ignore.sort()
		print(rounds_to_ignore)
		print(blacklist)
		print('\n-------------------------------------------\n\n')
