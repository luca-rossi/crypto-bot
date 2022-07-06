import pandas as pd
from modules.blockchain.contract import Contract
from modules.data.epochs_loader import EpochsLoader
from modules.data.tx_loader import TxLoader
from utils.config import Files
from utils.const import IndicatorPreds

class DataLoader:
	'''
	Load the data from the contract and the dataframes for the simulator.
	'''
	contract = None

	def __init__(self):
		'''
		Load the contract.
		'''
		self.contract = Contract()

	def load(self, min_epoch=None, max_epoch=None, save_every=50, update=True, process=False):
		'''
		Loads the datasets (epochs and transactions). Epochs need to be loaded before transactions.
		'''
		# TODO move the content of DataProcessor.get_processed_data here and add process param
		# TODO remove DataProcessor and call the processing here, which will be done in EpochsLoader and TxLoader
		epochs_loader = EpochsLoader()
		tx_loader = TxLoader()
		df_epochs = epochs_loader.load_epochs(self.contract, min_epoch, max_epoch, save_every, update)
		df_tx = tx_loader.load_txs(self.contract, df_epochs, update)
		return df_epochs, df_tx

	def load_recs(self):
		'''
		Loads the history of tradingview recommendations.
		Not all epochs are here because these recommendations are collected in real-time.
		Since this just loads tradingview recommendations, custom recommendations are not included here.
		'''
		df = pd.read_csv(Files.LOG_HISTORY_REC)
		df = df.set_index('epoch')
		df = df.replace('IGNORE', IndicatorPreds.IGNORE)
		df = df.replace('OKAY', IndicatorPreds.OKAY)
		df = df.replace('BUY', IndicatorPreds.BET_BULL)
		df = df.replace('SELL', IndicatorPreds.BET_BEAR)
		df = df.replace('NEUTRAL', IndicatorPreds.NEUTRAL)
		# remove duplicates (they are created in rare cases, e.g. when connection is lost while updating the df)
		df = df.drop_duplicates()
		return df

	def load_inds(self):
		'''
		Loads the inds from the history dataframe and removes the duplicates (if any, it should not happen).
		'''
		df_ind = pd.read_csv(Files.LOG_HISTORY_IND)
		# remove duplicates (they are created in rare cases, e.g. when connection is lost while updating the df)
		df_ind = df_ind.drop_duplicates()
		df_ind = df_ind.set_index('epoch')
		return df_ind
