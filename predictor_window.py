'''
Strategy based on deep (LSTM) neural networks (alternative implementation).
'''
# TODO refactor, move content to modules.predictor
import numpy as np
import pandas as pd
from keras.models import Sequential, load_model
from keras.layers import Dense
from keras.regularizers import l2
from utils.config import Files

normalize_price = [
	'v_close_1m', 'v_open_1m', 'v_low_1m', 'v_high_1m',
	'v_EMA5_1m', 'v_SMA5_1m', 'v_EMA10_1m', 'v_SMA10_1m', 'v_EMA20_1m', 'v_SMA20_1m', 'v_EMA30_1m', 'v_SMA30_1m',
	'v_EMA50_1m', 'v_SMA50_1m', 'v_EMA100_1m', 'v_SMA100_1m', 'v_EMA200_1m', 'v_SMA200_1m', 'v_Ichimoku.BLine_1m', 'v_VWMA_1m', 'v_HullMA9_1m',
	'v_close_5m', 'v_open_5m', 'v_low_5m', 'v_high_5m',
	'v_EMA5_5m', 'v_SMA5_5m', 'v_EMA10_5m', 'v_SMA10_5m', 'v_EMA20_5m', 'v_SMA20_5m', 'v_EMA30_5m', 'v_SMA30_5m',
	'v_EMA50_5m', 'v_SMA50_5m', 'v_EMA100_5m', 'v_SMA100_5m', 'v_EMA200_5m', 'v_SMA200_5m', 'v_Ichimoku.BLine_5m', 'v_VWMA_5m', 'v_HullMA9_5m',
	'v_close_15m', 'v_open_15m', 'v_low_15m', 'v_high_15m',
	'v_EMA5_15m', 'v_SMA5_15m', 'v_EMA10_15m', 'v_SMA10_15m', 'v_EMA20_15m', 'v_SMA20_15m', 'v_EMA30_15m', 'v_SMA30_15m',
	'v_EMA50_15m', 'v_SMA50_15m', 'v_EMA100_15m', 'v_SMA100_15m', 'v_EMA200_15m', 'v_SMA200_15m', 'v_Ichimoku.BLine_15m', 'v_VWMA_15m', 'v_HullMA9_15m',
]
#'lock_price'

MODE_EVAL = False
CONF = 0.7
WINDOW = 5
N_HIDDEN = 8
N_EPOCHS = 200
BATCH_SIZE = 64
TRAIN_TEST_SPLIT = 0.6
VAL_SPLIT = 0.3

df = None
if MODE_EVAL:
	df = pd.read_csv(Files.DATA_WINDOW)
	df = df.drop('Unnamed: 0', axis=1)
else:
	# load dataset and split it into train and test
	df = pd.read_csv(Files.DATA_EPOCHS)
	df2 = pd.DataFrame()
	for i in range(WINDOW):
		n = WINDOW - i
		df2['close' + str(n)] = df['close_price'].shift(n)
	df2['close'] = df['close_price']
	# for col in df2.columns:
	# 	# if col in normalize_price:
	# 	if col != 'close':
	# 		df2[col] = 100 * df2[col] / df2['close']
	for i in range(WINDOW):
		if i < WINDOW - 1:
			df2['close' + str(i + 1)] = (df2['close' + str(i + 1)] - df2['close' + str(i + 2)]) / 100
		else:
			df2 = df2.drop('close' + str(i + 1), axis=1)
	df2 = df2.drop('close', axis=1)
	df2['next_bet'] = df['next_bet']
	# df2 = df2[df2['close'] != 0]
	df2 = df2.replace([np.inf, -np.inf], np.nan)
	df2 = df2.dropna()
	df = df2
	df.to_csv(Files.DATA_WINDOW)
X_dataset = df.iloc[:, :-1]
Y_dataset = df.iloc[:, -1]
# scaler = StandardScaler()
# X_dataset = pd.DataFrame(scaler.fit_transform(X_dataset), columns=X_dataset.columns)
X_train = X_dataset.iloc[:int(X_dataset.shape[0] * TRAIN_TEST_SPLIT)]
X_test = X_dataset.iloc[int(X_dataset.shape[0] * TRAIN_TEST_SPLIT):]
Y_train = Y_dataset.iloc[:int(Y_dataset.shape[0] * TRAIN_TEST_SPLIT)]
Y_test = Y_dataset.iloc[int(Y_dataset.shape[0] * TRAIN_TEST_SPLIT):]
print(df)
print(X_dataset)
print(Y_dataset)
print(X_train)
print(Y_train)
if not MODE_EVAL:
	model = Sequential()
	model.add(Dense(N_HIDDEN, input_dim=X_dataset.shape[1], kernel_regularizer=l2(0.01), activation='relu'))
	# model.add(Dense(200, input_dim=X_dataset.shape[1], kernel_regularizer=l2(0.01)))
	# # model.add(BatchNormalization())
	# model.add(Dropout(0.4))
	# model.add(Activation('relu'))
	# model.add(Dense(100, input_dim=X_dataset.shape[1], kernel_regularizer=l2(0.01)))
	# # model.add(BatchNormalization())
	# model.add(Dropout(0.4))
	# model.add(Activation('relu'))
	# model.add(Dense(50, input_dim=X_dataset.shape[1], kernel_regularizer=l2(0.01)))
	# model.add(Activation('relu'))
	model.add(Dense(1, activation='sigmoid'))
	model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
	# model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])
	model.summary()
	hist = model.fit(X_train, Y_train, batch_size=BATCH_SIZE, epochs=N_EPOCHS, validation_split=VAL_SPLIT)
	model.save(Files.MODEL_WINDOW)
model = load_model(Files.MODEL_WINDOW)
pred = model.predict(X_test)
print(Y_test)
count = 0
correct = 0
w_correct = 0
for i in range(len(pred)):
	pred_el = pred[i][0]
	# actual_el = Y_test.iloc[i]
	actual_el = Y_test.iloc[i]#, 1]
	# payout = P_test.iloc[i]
	# payout = Y_test.iloc[i, 0]
	round_pred_el = None
	# print()
	# print(str(pred_el) + ' - ' + str(actual_el))
	if pred_el > CONF:
		round_pred_el = 1
	elif pred_el < 1 - CONF:
		round_pred_el = 0
	else:
		continue
	print()
	print(str(pred_el) + ' - ' + str(actual_el))# + ' payout ' + str(payout))
	if round_pred_el == actual_el:
		print('ok')
		correct += 1
		# w_correct += payout
	count += 1
accuracy = correct / count
# w_accuracy = w_correct / count
print('train shape')
print(X_train.shape)
print('test shape')
print(X_test.shape)
print('count')
print(count)
print('accuracy')
print(accuracy)
# print('w_accuracy')
# print(w_accuracy)
