import numpy as np
import random
from collections import deque
from keras.models import load_model, Sequential
from keras.layers import Dense
from tensorflow.keras.optimizers import Adam

class Agent():
	'''
	Very basic reinforcement learning agent (based on DQN) that learns how to make profitable predictions. At each round, it will choose one of the following actions: BetBull, BetBear, or Sit.
	'''

	def __init__(self, state_size, is_eval=False, action_size=3, model_name='agent.h5'):
		'''
		Initializes the agent.
		'''
		# TODO parametrize the following
		self.state_size = state_size			# normalized previous days
		self.action_size = action_size			# 3 elements in the action space: BetBull, BetBear, and Sit
		self.memory = deque(maxlen=100)			# set the experience replay memory to deque with 1000 elements inside it
		self.model_name = model_name
		self.is_eval = is_eval
		self.gamma = 0.95						# discounting parameter
		self.epsilon = 1.0						# exploration parameter (choose a random action or use the model): it starts at 1.0 so it only takes random actions at the beginning
		self.epsilon_final = 0.01				# final value of the exploration parameter (when the model is trained, it will do little exploration)
		self.epsilon_decay = 0.995				# rate at which the exploration parameter decreases
		self.model = load_model(model_name) if is_eval else self.__model()

	def __model(self):
		'''
		Defines the neural network.
		'''
		# TODO consider LSTM
		model = Sequential()
		# the input is a state
		model.add(Dense(units=int(self.state_size / 2 + 10), input_dim=self.state_size, activation="relu"))
		# the output layer consists of 3 neurons (one for each action)
		model.add(Dense(self.action_size, activation="linear"))
		model.compile(loss="mse", optimizer=Adam(lr=0.01))
		return model

	def action(self, state):
		'''
		Takes the state as input and returns an action to perform in that state.
		'''
		# produce a random number: if lower than epsilon, return a random action
		if not self.is_eval and np.random.rand() <= self.epsilon:
			return random.randrange(self.action_size)
		# if greater than epsilon, use the model to choose the action, return the (index of the) action with the highest expected reward
		return np.argmax(self.model.predict(state)[0])

	def exp_replay(self, batch_size):
		'''
		Experience replay: takes a batch of saved data and trains the model on that.
		'''
		# TODO parallelize this for GPU training
		# randomly select data from the experience replay memory
		mini_batch = random.sample(self.memory, batch_size)
		# iterate through each batch (state, action, reward, next_state, done) to train the model
		for state, action, reward, next_state, done in mini_batch:
			q_target_value = reward
			# if the agent is not in a terminal state, calculate the discounted total reward as the current reward
			if not done:
				q_target_value = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
			# predict the action and fit the model, construct the target vector as follows:
			# 1. use the current model to output the Q-value predictions
			target_actions = self.model.predict(state)
			# 2. rewrite the value of the chosen action with the computed target ("actual" reward)
			target_actions[0][action] = q_target_value
			# 3. use vectors in the objective computation (fit the model so it learns a more accurate expected reward for the chosen action)
			history = self.model.fit(state, target_actions, epochs=1, verbose=0)
		# decrease the epsilon parameter to slowly stop performing random actions
		if self.epsilon > self.epsilon_final:
			self.epsilon *= self.epsilon_decay
		return history.history['loss'][0]
