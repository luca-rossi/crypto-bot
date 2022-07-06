import os
import pandas as pd
from utils.config import Files, SimulatorSettings
from utils.const import Data

class EpochsLoader:
	'''
	Loads the epochs from the contract.
	'''

	def load_epochs(self, contract, min_epoch=None, max_epoch=None, save_every=50, update=True):
		'''
		Loads epochs from the contract, if they are not saved yet. They are stored in a csv file.
		'''
		if update:
			# init min epoch and current epoch (as the one before the min epoch so we can load that epoch)
			min_epoch = min_epoch or SimulatorSettings.MIN_EPOCH
			epoch = min_epoch - 1
			# load the dataset if exists to resume creation from there (otherwise it will be created from scratch)
			first = False
			try:
				if os.path.exists(Files.LOG_EPOCHS):
					df = pd.read_csv(Files.LOG_EPOCHS)
					df = df.set_index('epoch') if not df.empty else df
					epoch = int(df.index[-1]) if not df.empty else 1
				else:
					first = True
					df = pd.DataFrame(columns=Data.COLUMNS_EPOCHS)
					df = df.set_index('epoch')
					df.to_csv(Files.LOG_EPOCHS, mode='w', header=True)
			except pd.errors.EmptyDataError as e:
				# TODO remove redundancy
				first = True
				df = pd.DataFrame(columns=Data.COLUMNS_EPOCHS)
				df = df.set_index('epoch')
				df.to_csv(Files.LOG_EPOCHS, mode='w', header=True)
				print(e)
			# loop through all epochs and load them from contract, the loop is infinite to allow for undefined max epoch
			# TODO PW dict with epoch as key
			epochs_list = []
			while True:
				epoch += 1
				# exit loop if we reached max_epoch, notice that this is done before loading a new epoch
				if max_epoch and epoch > max_epoch:
					break
				# every once in a while, the partial dataframe is saved to file, so we don't have to start again if we stop early
				if epoch % save_every == 0:
					df = pd.DataFrame(epochs_list)
					self.__save_partial_epochs(df, epoch)
					epochs_list = []
				# load epoch info from contract
				data = contract.load_epoch(epoch)
				# exit loop if we reached a "future" epoch, notice that this is done after a new epoch is loaded
				if data[0] == 0 and not first:
					break
				# if everything is okay, add the new epoch info to the temporary dataset
				epochs_list.append({
					'epoch': epoch,
					'start_time': data[1],
					'end_time': data[2],
					'lock_price': data[4] / 1000000,
					'close_price': data[5] / 1000000,
					'bull_amount': data[9] / 1000000000000000,
					'bear_amount': data[10] / 1000000000000000,
				})
			df = pd.DataFrame(epochs_list, columns=Data.COLUMNS_EPOCHS)
			# remove the last 2 epochs because they have not been updated yet
			if max_epoch is None:
				df = df[:-2]
			# save the last part of the dataset
			self.__save_partial_epochs(df, epoch)
		# load df again to get all epochs (between min and max)
		df = pd.read_csv(Files.LOG_EPOCHS)
		df = df.set_index('epoch') if not df.empty else df
		df = df.loc[min_epoch:max_epoch] if not df.empty else df
		return df

	def __save_partial_epochs(self, df, last_epoch):
		'''
		Appends the data loaded from the contract to the csv file.
		'''
		print('Epoch: ' + str(last_epoch))
		df = df.set_index('epoch') if not df.empty else df
		df.to_csv(Files.LOG_EPOCHS, mode='a', header=(not os.path.exists(Files.LOG_EPOCHS)))
		return df
