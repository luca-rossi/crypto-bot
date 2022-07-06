import numpy as np
import pandas as pd
from keras.models import Sequential, load_model
from keras.layers import Dense
from utils.config import Files
from utils.utils import Utils

class Predictor:
	'''
	Handles data loading, training, and evaluation of machine learning (mostly deep learning) models.
	'''
	# TODO refactor to Pytorch
	df = None
	X_dataset = None
	Y_dataset = None
	X_train = None
	X_test = None
	Y_train = None
	Y_test = None
	P_test = None			# payouts (for weighted evaluation of profitability)
	model = None

	def __init__(self, file_dataset, col_features=1, col_after_features=-1, col_target=-1, col_payout=None, is_ohlcv=False, train_test_split=0.7, save=False):
		'''
		Loads data and prepares it for training.
		'''
		# load dataset and process it
		self.df = pd.read_csv(file_dataset)
		self.df.replace([np.inf, -np.inf], np.nan, inplace=True)
		self.df.dropna(inplace=True)
		if is_ohlcv:
			self.df['open'] = Utils.sigmoid(self.df['open'] - self.df['open'].shift(1))
			self.df['high'] = Utils.sigmoid(self.df['high'] - self.df['high'].shift(1))
			self.df['low'] = Utils.sigmoid(self.df['low'] - self.df['low'].shift(1))
			self.df['close'] = Utils.sigmoid(self.df['close'] - self.df['close'].shift(1))
			self.df['volume'] = Utils.sigmoid(self.df['volume'] - self.df['volume'].shift(1))
			features = list(self.df.columns)
			for f in features:
				# create lags
				# TODO param lag size
				for lag in range(1, 5 + 1):
					col = f'{f}_lag_{lag}'
					self.df[col] = self.df[f].shift(lag)
			self.df['next_result'] = Utils.sigmoid(self.df['close'] - self.df['close'].shift(-5))
		self.df = self.df.replace('SELL', 1)
		self.df = self.df.replace('NEUTRAL', 2)
		self.df = self.df.replace('BUY', 3)
		# drop some rows based on trend conditions to simplify training
		# drop_cond1 = ((self.df['ratio_ema50'] > 1) & (self.df['ratio_ema100'] < 1)) 
		# drop_cond2 = ((self.df['ratio_ema50'] < 1) & (self.df['ratio_ema100'] > 1)) 
		# drop_cond = drop_cond1 | drop_cond2
		# self.df = self.df.drop(self.df[drop_cond].index)
		self.df = self.df.drop(self.df[self.df['lock_price'] < 0.010].index)
		# split features and target (last 3 columns: lock_price, result, close_price)
		self.X_dataset = self.df.iloc[:, col_features:col_after_features]
		self.Y_dataset = self.df.iloc[:, col_target]
		# save dataset
		if save:
			self.df.to_csv(Files.DATA_PREP)
		# split dataset into train and test
		self.X_train = self.X_dataset.iloc[:int(self.X_dataset.shape[0] * train_test_split)]
		self.X_test = self.X_dataset.iloc[int(self.X_dataset.shape[0] * train_test_split):]
		self.Y_train = self.Y_dataset.iloc[:int(self.Y_dataset.shape[0] * train_test_split)]
		self.Y_test = self.Y_dataset.iloc[int(self.Y_dataset.shape[0] * train_test_split):]
		# get payouts
		if col_payout:
			P_dataset = self.df.iloc[:, col_payout]
			self.P_test = P_dataset.iloc[int(P_dataset.shape[0] * train_test_split):]
		# print shapes
		print(self.X_train.shape)
		print(self.Y_train.shape)
		print(self.X_test.shape)
		print(self.Y_test.shape)
		print('-----------------------')

	def add_target(self, load_path=None, steps=1, save_path=None, save=False):
		'''
		Prepares data in a way that is suitable for predictors (with the next bet as target).
		'''
		df = pd.read_csv(load_path or Files.LOG_EPOCHS)
		df = df.set_index('epoch')
		df['next_result'] = df['close_price'].shift(-steps) - df['lock_price'].shift(-1)
		df.loc[df['next_result'] > 0, 'next_result'] = 1		# 1 = bull
		df.loc[df['next_result'] < 0, 'next_result'] = 0		# 0 = bear
		df = df[:-1]
		print(df)
		if save_path or save:
			df.to_csv(save_path or Files.DATA_EPOCHS)
		return df

	def build_model_cls(self, negative_output=False):
		'''
		Builds a classifier model (it minimizes the binary crossentropy loss).
		'''
		activation = 'tanh' if negative_output else 'sigmoid'
		self.model = Sequential()
		self.model.add(Dense(units=32, input_dim=self.X_train.shape[1], activation='relu'))
		self.model.add(Dense(units=1, activation=activation))
		self.model.compile(optimizer='adam', loss='binary_crossentropy')
		self.model.summary()
		return self.model

	def build_model_regr(self):
		'''
		Builds a regression model (it minimizes the mean squared error loss).
		'''
		self.model = Sequential()
		self.model.add(Dense(units=32, input_dim=self.X_train.shape[1], activation='relu'))
		self.model.add(Dense(units=1))
		self.model.compile(optimizer='adam', loss='mse')
		self.model.summary()
		return self.model

	def train_model(self, epochs=50, batch_size=32, validation_split=0.25, load=False, save=True):
		'''
		Trains the model (or loads it from a file).
		'''
		if load:
			self.model = load_model(Files.MODEL_H5)
		else:
			self.model.fit(self.X_train, self.Y_train, epochs, batch_size, validation_split)
		if save:
			self.model.save(Files.MODEL)
		return self.model

	def evaluate(self, conf=0.6):
		'''
		Evaluates the model. The prediction is valid only if the confidence is greater than the given threshold.
		'''
		# TODO def train_and_evaluate(self, model, X_test, Y_test, P_test=None, conf=0.6):
		# TODO test with weighted accuracy
		preds = self.model.predict(self.X_test)
		print(preds)
		print(self.Y_test)
		count = 0
		correct = 0
		# w_correct = 0
		for i in range(len(preds)):
			pred = preds[i][0]
			result = self.Y_test[i]
			# payout = self.P_test[i]
			if pred > conf:
				if result == 1:
					correct += 1
					# w_correct += payout
				count += 1
			elif pred < 1 - conf:
				if result == 0:
					correct += 1
					# w_correct += payout
				count += 1
		print()
		print('Count')
		print(count)
		print('Accuracy')
		print(correct / count)
		print('Weighted accuracy')
		# print(w_correct / count)
