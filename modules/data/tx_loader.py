import os
import random
import time
import traceback
import pandas as pd
from utils.config import Files, StrategyParams
from utils.const import Const, ContractMethods, Data, Transactions

class TxLoader:
	'''
	Loads the transactions on the contract.
	'''

	def load_txs(self, contract, df_ep=None, update=True):
		'''
		Loads the transaction history from the contract. If the transaction history is not yet saved, it saves it. Otherwise, if the transaction history is already saved, it loads it.
		It also saves the transaction history to a csv file and returns it as a dataframe sorted by epoch.
		For each epoch, it loads the transaction history from the contract and adds it to the temporary dataset. Then, it saves the temporary dataset to a csv file.
		Finally, it loads the temporary dataset and adds it to the final dataset.
		It also increments the value of epoch to match epochs_data.
		'''
		# TODO this is a long method, maybe it should be split into smaller methods. Also it's very messy, some things are done manually, needs fixing and refactoring.
		if update:
			# TODO this is a hack, it should be done in a better way
			# in manual mode, we choose the starting block and the block is incremented forcefully at every iteration
			# needed when there are long pauses in the contract and the loader gets stuck loading the same blocks
			MANUAL_MODE = False
			CHECKPOINT = 1#13103595			# the block0 where to start loading the transactions (will not be needed after fixing this code)
			last_block = 1					# BNB: 10333825 - CAKE: 17760782 - first block (contract creation)
			last_timestamp = 0				# used to check if we reached the end (or a long pause)
			# load epochs dataset if not provided
			if df_ep is None:
				df_ep = pd.read_csv(Files.LOG_EPOCHS)
			last_epoch = 0
			# load last epoch from saved dataset
			# if os.path.exists(Files.LOG_TXS):
			# 	try:
			# 		df = pd.read_csv(Files.LOG_TXS)
			# 		last_epoch = df.iloc[-1]['epoch']
			# 		last_block = df.iloc[-1]['blockNumber']
			# 		last_timestamp = df.iloc[-1]['timeStamp']
			# 	except pd.errors.EmptyDataError as e:
			# 		print(e)
			try:
				if os.path.exists(Files.LOG_TXS):
					df = pd.read_csv(Files.LOG_TXS)
					last_epoch = df.iloc[-1]['epoch'] if not df.empty else last_epoch
					last_block = df.iloc[-1]['blockNumber'] if not df.empty else last_block
					last_timestamp = df.iloc[-1]['timeStamp'] if not df.empty else last_timestamp
				else:
					df = pd.DataFrame(columns=Data.COLUMNS_TXS)
					df.to_csv(Files.LOG_TXS, mode='w', header=True)
			except pd.errors.EmptyDataError as e:
				# TODO remove redundancy
				df = pd.DataFrame(columns=Data.COLUMNS_TXS)
				df.to_csv(Files.LOG_TXS, mode='w', header=True)
				print(e)
			if MANUAL_MODE:
				last_block = 13104090	# 13104100 block after long pause
			# read txs until the end
			count = 1
			while True:
				try:
					# this is just a security check to avoid that the file is overwritten with an empty one
					if int(last_block) < CHECKPOINT:
						print('Checkpoint')
						print('Last block: ' + str(last_block))
						print('Possible trouble ahead, exiting...')
						exit(0)
					# get df with latest 10000 txs
					txs = contract.get_txs_from_block(last_block)
					# skip if timeout
					if txs is None:
						continue
					df = pd.json_normalize(txs)
					# TODO a version similar to this should be a partial fix for the problem of the loader getting stuck
					# if len(df) == 0:
					# 	last_block += 1
					# 	print(last_block)
					# 	continue
					# keep only the txs that are bets
					filter_bet_bull = df['input'].str.contains(ContractMethods.BULL_METHOD)
					filter_bet_bear = df['input'].str.contains(ContractMethods.BEAR_METHOD)
					df = df[filter_bet_bull | filter_bet_bear]
					df.loc[filter_bet_bull, 'input'] = Transactions.BET_BULL
					df.loc[filter_bet_bear, 'input'] = Transactions.BET_BEAR
					# drop errors
					df = df[(df['isError'] == '0') & (df['txreceipt_status'] == '1')]
					# normalize values
					# print(df['value'])
					df['value'] = df['value'].str[:-15].astype('int64') / 1000
					# only keep interesting data
					df = df[['blockNumber', 'timeStamp', 'from', 'value', 'input']]#.reset_index(drop=True)
					# get tx epochs by iterating epochs log (important: all epochs must be loaded before txs)
					# TODO could probably be vectorized, build it dynamically using concat (and copy to defragment it)
					df['epoch'] = 0
					df['start_time'] = 0
					df['timeStamp'] = df['timeStamp'].astype('int64')
					for epoch, epoch_data in df_ep.loc[last_epoch:].iterrows():
						filter_min_epoch = df['timeStamp'] >= int(epoch_data['start_time'])
						if len(df[filter_min_epoch]) == 0:
							print('Last epoch: ' + str(epoch))
							last_epoch = epoch - 1
							break
						df.loc[filter_min_epoch, 'epoch'] = epoch
						df.loc[filter_min_epoch, 'start_time'] = epoch_data['start_time']
					df['time'] = df['timeStamp'] - df['start_time']
					# drop txs happened in epochs that haven't been loaded yet (in the unlikely scenario where a new epoch starts after loading epochs and before loading txs)
					df = df[df['time'] < Const.ROUND_DURATION]
					# save info about last tx for next iteration
					last_block = int(df.iloc[-1]['blockNumber'])
					new_timestamp = int(df.iloc[-1]['timeStamp'])
					# if the new timestamp and the last timestamp are the same, no new transactions have been loaded, which means that the dataset is fully loaded (or a long pause has been reached)
					if new_timestamp == last_timestamp:
						# df = self.__clean_saved_txs()
						print('All txs loaded (or long pause reached)')
						break
					last_timestamp = new_timestamp
					# save the dataset and drop duplicates sometimes
					df.to_csv(Files.LOG_TXS, mode='a', index=False, header=(not os.path.exists(Files.LOG_TXS)))
					if count % 20 == 0:
						self.__clean_saved_txs(save=True)
					count += 1
				except Exception as e:
					print(traceback.format_exc())
					time.sleep(1)
					if MANUAL_MODE:
						last_block += 1
					print('Last block: ' + str(last_block))
		# the returned dataset has just been loaded
		df = self.__clean_saved_txs()
		df['epoch'] = df['epoch'] + 1
		return df

	def __clean_saved_txs(self, save=False):
		'''
		Loads the saved txs, cleans them, and sometimes saves them again.
		'''
		# TODO it should be made clearer that this also returns an updated dataset that has just been loaded
		print('Loading txs for cleaning...')
		df = pd.read_csv(Files.LOG_TXS)
		# TODO PW optimize (df.iloc...)
		print('Cleaning txs...')
		df = df.drop_duplicates()
		rnd = random.random()
		if save or StrategyParams.SAVE_UPDATED_TXS or (rnd < StrategyParams.SAVE_UPDATED_TXS_P):
			print('Saving clean txs... ' + str(round(rnd, 2)))
			df.to_csv(Files.LOG_TXS, mode='w', index=False, header=True)
		return df
