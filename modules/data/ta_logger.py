import os
import pandas as pd
from utils.config import Files
from utils.const import Data

class TALogger:
	'''
	Saves the tradingview predictions to files, both recs and inds. Not used with the current strategy.
	Handles splitting and merging of the files (not necessary, but can be practical sometimes).
	'''
	analysis = None

	def update_analysis(self, analysis):
		'''
		Updates the tradingview analysis.
		'''
		self.analysis = analysis

	def save_predictions_to_file(self, epoch):
		'''
		Saves the predictions to files (both recs and inds).
		'''
		if not self.analysis:
			return
		# save recommendations to csv for selected timeframes
		self.__save_recs(epoch, Data.TIMEFRAMES, Files.LOG_HISTORY_REC)
		# save indicator values to csv for selected timeframes
		self.__save_inds(epoch, Data.TIMEFRAMES, Files.LOG_HISTORY_IND)
		# save recommendations to csv for all timeframes
		self.__save_recs(epoch, Data.ALL_TIMEFRAMES, Files.LOG_HISTORY_REC_ALL)
		# save indicator values to csv for all timeframes
		self.__save_inds(epoch, Data.ALL_TIMEFRAMES, Files.LOG_HISTORY_IND_ALL)

	def __save_inds(self, epoch, timeframes, file):
		'''
		Saves the tradingview technical indicator values.
		'''
		pred_ind = {}
		pred_ind['epoch'] = epoch
		# pred_rec['epoch'] = pred_rec['epoch'].astype(int)
		for tf in timeframes:
			for key, value in self.analysis[tf].indicators.items():
				pred_ind[key + '_' + tf] = value
		columns = list(pred_ind.keys())
		df = pd.DataFrame(columns=columns)
		df = df.append(pred_ind, ignore_index=True)
		df = df.set_index('epoch')
		df.to_csv(file, mode='a', header=(not os.path.exists(file)))

	def __save_recs(self, epoch, timeframes, file):
		'''
		Saves the tradingview recommendations based on technical indicators.
		'''
		pred_rec = {}
		pred_rec['epoch'] = epoch
		# pred_rec['epoch'] = pred_rec['epoch'].astype(int)
		for tf in timeframes:
			for key, value in self.analysis[tf].oscillators['COMPUTE'].items():
				pred_rec[key + '_' + tf] = value
			for key, value in self.analysis[tf].moving_averages['COMPUTE'].items():
				pred_rec[key + '_' + tf] = value
		columns = list(pred_rec.keys())
		df = pd.DataFrame(columns=columns)
		df = df.append(pred_rec, ignore_index=True)
		df = df.set_index('epoch')
		df.to_csv(file, mode='a', header=(not os.path.exists(file)))

	def split_files(self):
		'''
		Splits a csv file into smaller chunks.
		'''
		# split csv
		for i in range(len(Files.SPLIT_FILES)):
			file = Files.SPLIT_FILES[i]
			directory = Files.SPLIT_DIRS[i]
			# make a destination folder if it doesn't exist yet
			print(file)
			if not os.path.exists(directory):
				os.mkdir(directory)
			else:
				# otherwise clean out all files in the destination folder
				for new_file in os.listdir(directory):
					os.remove(os.path.join(directory, new_file))
			df = pd.read_csv(file)
			for n in range(0, len(df), Files.SPLIT_CHUNK_SIZE):
				ix = int(n / Files.SPLIT_CHUNK_SIZE)
				part = df.iloc[n:n+Files.SPLIT_CHUNK_SIZE, :]
				filename = os.path.join(directory, ('part%003d.csv' % ix))
				part.to_csv(filename)
				print(ix)
		print('---------------------------------------')
		# split csv with complete analysis
		for i in range(len(Files.SPLIT_FILES_ALL)):
			file = Files.SPLIT_FILES_ALL[i]
			directory = Files.SPLIT_DIRS_ALL[i]
			print(file)
			# make a destination folder if it doesn't exist yet
			if not os.path.exists(directory):
				os.mkdir(directory)
			else:
				# otherwise clean out all files in the destination folder
				for new_file in os.listdir(directory):
					os.remove(os.path.join(directory, new_file))
			df = pd.read_csv(file)
			for n in range(0, len(df), Files.SPLIT_CHUNK_SIZE_ALL):
				ix = int(n / Files.SPLIT_CHUNK_SIZE_ALL)
				part = df.iloc[n:n+Files.SPLIT_CHUNK_SIZE_ALL, :]
				filename = os.path.join(directory, ('part%003d.csv' % ix))
				part.to_csv(filename)
				print(ix)

	def merge_files(self):
		'''
		Merges the split csv files (by the split_files method) into one file.
		'''
		# TODO include SPLIT_FILES_ALL
		for i in range(len(Files.SPLIT_FILES)):
			file = Files.SPLIT_FILES[i]
			directory = Files.SPLIT_DIRS[i]
			# create a new destination file
			output_file = open(file, 'wb')
			# get a list of the file parts
			parts = os.listdir(directory)
			# sort them by name (remember that the order num is part of the file name)
			parts.sort()
			# go through each portion one by one
			for file in parts:
				# assemble the full path to the file
				path = os.path.join(directory, file)
				print(path)
				# open the part
				input_file = open(path, 'rb')
				while True:
					# read all bytes of the part
					bytes = input_file.read(Files.SPLIT_CHUNK_SIZE)
					# break out of loop if we are at end of file
					if not bytes:
						break
					# write the bytes to the output file
					output_file.write(bytes)
				input_file.close()
			output_file.close()
