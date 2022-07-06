'''
Strategy based on deep (LSTM) neural networks.
'''
# TODO refactor, move content to modules.predictor
import argparse
import numpy as np
import pandas as pd
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout
from modules.predictor import Predictor
from utils.config import Files

parser = argparse.ArgumentParser()
parser.add_argument('--train_split', '-s', type=float, default=0.7, help='fraction of data to use for training')
parser.add_argument('--epochs', '-e', type=int, default=50, help='number of epochs to train')
parser.add_argument('--batch_size', '-b', type=int, default=32, help='batch size')
parser.add_argument('--timesteps', '-t', type=int, default=15, help='number of past timesteps for feature augmentation')
parser.add_argument('--conf', '-c', type=float, default=0.6, help='minimum confidence required to consider a prediction')
args = parser.parse_args()

predictor = Predictor(Files.DATA_BINANCE_OHLC_1M)

# load dataset and split it into train and test
df = pd.read_csv(Files.DATA_BINANCE_OHLC_1M)
df['close_5m_future'] = df['close'].shift(-5)
df['close_1m_past'] = df['close'].shift(1)
df['increment'] = 100 * (df['close'] / df['close_1m_past'] - 1)
df['next_result'] = 100 * (df['close_5m_future'] / df['close'] - 1)
df.loc[(df['next_result'] > 0), 'next_result'] = 1
df.loc[(df['next_result'] <= 0), 'next_result'] = 0
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.dropna(inplace=True)
size = df.shape[0]
df_x = df.iloc[:, -2]
df_y = df.iloc[:, -1]

# format dataset for LSTM
df_X = []
df_Y = []
for i in range(args.timesteps, df_x.shape[0]):
	df_X.append(df_x[i-args.timesteps:i])
	df_Y.append(df_y[i])
df_X, df_Y = np.array(df_X), np.array(df_Y)
# df_X = np.reshape(df_X, (df_X.shape[0], df_X.shape[1], 1))
X_train = df_X[:int(size * args.train_split)]
Y_train = df_Y[:int(size * args.train_split)]
X_test = df_X[int(size * args.train_split):]
Y_test = df_Y[int(size * args.train_split):]

print(df_X)
print(df_Y)
print('-----------------------')
print(X_train.shape)
print(Y_train.shape)
print(X_test.shape)
print(Y_test.shape)
print('-----------------------')

# build LSTM model
model = Sequential()
model.add(LSTM(units=16, return_sequences=False, input_shape=(df_X.shape[1], 1), activation='tanh'))
model.add(Dense(units=1, activation='tanh'))
model.compile(optimizer='adam', loss='binary_crossentropy')
# model.add(Dense(units=1, activation='tanh'))
# model.compile(optimizer='adam', loss='mean_squared_error')
model.summary()

# fit model
model.fit(X_train, Y_train, epochs=args.epochs, batch_size=args.batch_size, validation_split=0.25)

# save model
model.save(Files.MODEL)

# from keras.models import load_model
# model = load_model(Files.MODEL)

# predict
# df = pd.concat((x_train, x_test), axis = 0)
# inputs = df[len(x_train) - len(x_test) - args.timesteps:].values			 # so the test set has args.timesteps previous entries to make the prediction
# inputs = inputs.reshape(-1, 1)
# X_test = []
# for i in range(args.timesteps, x_test.shape[0]):
# 	X_test.append(inputs[i-args.timesteps:i, 0])
# X_test = np.array(X_test)
# X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
predictor.evaluate(conf=args.conf)
