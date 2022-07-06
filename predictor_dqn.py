'''
Strategy based on reinforcement learning (DQN).
'''
# TODO general refactor, move content to modules/predictor/environment.py and modules/predictor/agent.py, refactor to Pytorch
import numpy as np
from tqdm import tqdm
from modules.predictor.agent import Agent
from modules.predictor.environment import Environment
from utils.config import Files

# TODO args
BET_AMOUNT = 20
IDLE_PENALTY_INCREMENT = 0.1
FEE = 2
FEE_REL = 0.97
WINDOW_SIZE = 50
N_EPISODES = 1000
BATCH_SIZE = 64

# TODO generate from Environment
# def get_state(data, timestep, window_size):
#	'''
#	Create the state with a given window state (e.g. window_size = 5: 5 states to predict the target/action)
#	'''
# 	# close = data['close'].to_numpy()
# 	# # Update the input states as differences in stock prices (price changes over time)
# 	# starting_id = timestep - window_size + 1
# 	# # If the starting_id is positive create a state, if it is negative append the info until we get to the window_size
# 	# block = close[starting_id:timestep + 1] if starting_id >= 0 else -starting_id * [close[0]] + list(close[0:timestep + 1])		# pad with t0
# 	# # print(starting_id)
# 	# # print(block)
# 	# # Define an empty list called state and iterate through the window_data list
# 	# state = []
# 	# for i in range(window_size - 1):
# 	# 	# Normalize the price data with the sigmoid function
# 	# 	val = 0
# 	# 	try:
# 	# 		# val = Utils.sigmoid(block[i + 1] - block[i])
# 	# 		val = 100 * (block[i + 1] - block[i]) / block[i]
# 	# 	except OverflowError:
# 	# 		val = 0
# 	# 	state.append(val)
# 	# return np.array([state])
# 	return np.array([data.iloc[timestep, :-1]])

# TODO try overfitting current solution with DQN (just to see if it works, only include current inds). Also, include volumes and 1-minute data.
environment = Environment()
# data, payouts = environment.generate()						# TODO generate environment
data, payouts = environment.load_dataset_inds(rec_only=False)
print(data)
data_samples = len(data) - 1
idle_penalty = 0				# starting value
actions = {0: 'Sit', 1: 'Bet Bull', 2: 'Bet Bear'}
# define the agent
agent = Agent(data.shape[1] - 1)
agent.model.summary()
# iterate through all the episodes to train the model
for episode in range(1, N_EPISODES + 1):
	print("Episode: {}/{}".format(episode, N_EPISODES))
	# define the initial state with get_state
	state = environment.get_state(data, 0, WINDOW_SIZE + 1)
	# keep track of total_profit
	total_profit = 0
	n_iter = 0
	bets_count = 0
	correct = 0
	w_correct = 0
	# define the timestep and iterate
	for t in tqdm(range(data_samples)):
		print('..............................................')
		print(t)
 		# define action, next_state, and reward
		action = agent.action(state)
		n_iter += 1
		# sitting
		next_state = environment.get_state(data, t + 1, WINDOW_SIZE + 1)
		reward = 0
		profit = 0
		# TODO get payout from the environment
		# payout = environment.get_payout(t)
		# update the state based on the action
		if action == 1:								# BetBull
			bets_count += 1
			# if data['close'][t + 1] > data['close'][t]:
			if data['result'][t] == 1:
				profit = BET_AMOUNT * payouts[t] * FEE_REL - FEE
				reward = profit
				correct += 1
				w_correct += payouts[t]
				# print('BetBull - Win')
			else:
				profit = - BET_AMOUNT - FEE
				reward = profit
				# print('BetBull - Lose')
			idle_penalty = 0
		elif action == 2:							# BetBear
			bets_count += 1
			# if data['close'][t + 1] < data['close'][t]:
			if data['result'][t] == 0:
				profit = BET_AMOUNT * payouts[t] * FEE_REL - FEE
				reward = profit
				correct += 1
				w_correct += payouts[t]
				# print('BetBear - Win')
			else:
				profit = - BET_AMOUNT - FEE
				reward = profit
				# print('BetBear - Lose')
			idle_penalty = 0
		else:										# Sit
			reward = - idle_penalty
			idle_penalty += IDLE_PENALTY_INCREMENT
		total_profit += profit
		# check if this is the last sample in the dataset
		done = (t == data_samples - 1)
		# append all of the data to our agent's experience replay buffer
		agent.memory.append((state, action, reward, next_state, done))
		# change the state to the next_state so we can iterate through the whole episode
		state = next_state
		# print out the total_profit when done
		if done:
			print("\n--------------------------------")
			print("TOTAL PROFIT: {}".format(total_profit))
			print("--------------------------------")
		# experience replay
		if len(agent.memory) > BATCH_SIZE and n_iter % BATCH_SIZE == 0:
			loss = agent.exp_replay(BATCH_SIZE)
			accuracy = correct / bets_count
			w_accuracy = w_correct / bets_count
			print('Episode: {}\tProfit: {:.2f}\tAction: {}\tReward: {:.2f}\tTot: {}\tAcc: {:.2f}\tWacc: {:.2f}\tEpsilon: {:.2f}'.format(episode, total_profit, actions[action], reward, bets_count, accuracy, w_accuracy, agent.epsilon))
	# save the model
	# if episode % 10 == 0:
	agent.model.save(Files.MODEL_AGENT.format(episode))
# TODO evaluate
