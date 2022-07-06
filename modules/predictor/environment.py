import numpy as np
import pandas as pd
from modules.data.epochs_loader import EpochsLoader
from utils.config import Files

class Environment:
	'''
	Generates and handles the environment where the agent is playing.
	'''
	# TODO not implemented yet, will be used after refactoring the dqn part. The plan is to use this class to generate different kinds of environments and process data in different ways.
	data_loader = None
	epochs_data = None
	get_state = None			# function that will be dynamically generated according to the type of environment
	get_reward = None			# function that will be dynamically generated according to the type of environment

	def __init__(self, contract):
		epochs_loader = EpochsLoader()
		return epochs_loader.load_epochs(contract)

	def generate(self):
		'''
		Loads the data and generates the environment (as the two functions get_state and get_reward).
		'''
		# TODO implement this
		return

	def load_dataset_inds(self, rec_only=False):
		'''
		Loads the dataset and processes it to be used for training the agent.
		'''
		# TODO refactor, fix, remove redundancies (reuse code from the data module)
		if rec_only:
			df = pd.read_csv(Files.DATA_REC)
			df = df.drop('lock_price', axis=1)
			df.replace([np.inf, -np.inf], np.nan, inplace=True)
			df.dropna(inplace=True)
			df = df.replace('SELL', -1)
			df = df.replace('NEUTRAL', 0)
			df = df.replace('BUY', 1)
		else:
			df = pd.read_csv(Files.DATA_IND)
			df = df.drop('lock_price', axis=1)
			df.replace([np.inf, -np.inf], np.nan, inplace=True)
			df.dropna(inplace=True)
			df_ind = pd.read_csv(Files.LOG_HISTORY_IND)
		# TODO get payouts from epochs_data
		payouts = df.iloc[:, -3].to_numpy()
		data = pd.DataFrame()
		data = df.iloc[:, 1:-3]
		data['result'] = df.iloc[:, -2]
		print(data)
		# TODO move this to generate()
		def get_state(data, timestep, window_size):
			return np.array([data.iloc[timestep, :-1]])
		self.get_state = get_state
		return data, payouts
