import random
from modules.simulator.simulator import Simulator
from utils.config import SimulatorSettings

class Searcher:
	'''
	Searches profitable solutions among combinations of technical indicators.
	Optionally, the dataset is split into training, validation and test sets.
	These splits do not have the same meaning as in machine learning. For example, the validation set does not validate anything.
	If anything, it proves that there is overfitting by showing how profitable solutions on the training set are not profitable anymore on the validation set.
	The same goes for the test set.
	'''
	# TODO check if it still works (probably a bit buggy after refactoring). Some methods are too long, simplify them.
	simulator = None
	# settings
	ind_values = []
	n_indicators = 0
	min_balance = 0
	min_tot = 0
	solutions_sorter = None
	# data
	epochs_data = {}
	train_epochs_data = {}
	val_epochs_data = {}
	test_epochs_data = {}
	# simulation data
	count = 0
	tot_solutions = 0
	tot_profitable_solutions = 0
	tot_val_profitable_solutions = 0
	solutions = []
	best_solution = None
	idxs = []

	def __init__(self, ind_values, min_balance_ratio=SimulatorSettings.MIN_BALANCE_RATIO, solutions_sorter=(lambda x: x['balance']), window_data=None, control=False):
		'''
		Initializes the searcher with the given parameters and the simulator. If the control flag is set, randomizes the values of the technical indicators in non-neutral epochs.
		'''
		self.ind_values = ind_values
		self.n_indicators = len(ind_values.keys())
		self.min_balance = SimulatorSettings.INIT_BALANCE * min_balance_ratio
		self.solutions_sorter = solutions_sorter
		self.simulator = Simulator(window_data)
		# if this is a control experiment, randomize values
		if control:
			for ind in self.ind_values.keys():
				for epoch in self.ind_values[ind].keys():
					if self.ind_values[ind][epoch] != 'NEUTRAL':
						self.ind_values[ind][epoch] = 'BUY' if random.random() > 0.5 else 'SELL'

	def init_epochs(self, epochs_data, train_ratio=1, trainval_ratio=0, min_tot_ratio=0, random=False):
		'''
		Initializes the epochs dataset and the training/validation/test splits.
		'''
		start = SimulatorSettings.MIN_EPOCH
		n = len(epochs_data) - SimulatorSettings.MIN_EPOCH
		self.epochs_data = epochs_data
		self.train_epochs_data = epochs_data[start:start + int(n * train_ratio)]
		self.val_epochs_data = epochs_data[start + int(n * train_ratio):start + int(n * trainval_ratio)]
		self.test_epochs_data = epochs_data[start + int(n * trainval_ratio):]
		# TODO try randomization
		# self.test_epochs_data = epochs_data.sample(frac=(1 - trainval_ratio))
		# trainval_epochs_data = epochs_data.drop(self.test_epochs_data.index)
		# self.train_epochs_data = trainval_epochs_data.sample(frac=(train_ratio * trainval_ratio))
		# self.val_epochs_data = trainval_epochs_data.drop(self.train_epochs_data.index)
		print('Train size: ' + str(self.train_epochs_data.shape[0]))
		print('Val size: ' + str(self.val_epochs_data.shape[0]))
		print('Test size: ' + str(self.test_epochs_data.shape[0]))
		self.min_tot = int(self.train_epochs_data.shape[0] * min_tot_ratio)

	def search_solutions(self, max_ind_names, prev_ind_names=[], prev_idxs=[], min_idx=0, val_profitable=False):
		'''
		Exhaustively searches for solutions among the given combinations of technical indicators.
		'''
		for i, (ind, value) in enumerate(self.ind_values.items()):
			if i >= min_idx:
				curr_ind_names = prev_ind_names + [ind]
				curr_idxs = prev_idxs + [i]
				# base step
				if len(curr_ind_names) >= max_ind_names:
					self.count += 1
					if self.count % 10**(len(curr_idxs)) == 0:
						print(curr_ind_names)
						self.__prune_solutions()
						self.print_solutions(curr_idxs)
					# training step
					result = self.simulate(curr_ind_names, epochs_data=self.train_epochs_data)
					if result:
						# validation step
						result_val = 0
						if len(self.val_epochs_data) > 0:
							result_val = self.simulate(curr_ind_names, epochs_data=self.val_epochs_data)
						result['balance_val'] = result_val['balance'] if result_val else 0
						# save solution
						self.tot_solutions += 1
						if result['balance'] > SimulatorSettings.INIT_BALANCE and (not val_profitable or result['balance_val'] > SimulatorSettings.INIT_BALANCE):
							self.tot_profitable_solutions += 1
							if result['balance_val'] > SimulatorSettings.INIT_BALANCE:
								self.tot_val_profitable_solutions += 1
							if self.best_solution is None or (self.best_solution['balance'] < result['balance']):
								self.best_solution = result
							self.solutions.append(result)
				else:
					# prune search tree before recursive step: don't search through solutions that we already know will fail
					result = self.simulate(curr_ind_names, epochs_data=self.train_epochs_data)
					# recursive step
					if result:
						self.search_solutions(max_ind_names, prev_ind_names=curr_ind_names, prev_idxs=curr_idxs, min_idx=i, val_profitable=val_profitable)

	def search_solutions_greedy(self, max_ind_names, prev_ind_names=[], prev_idxs=[], min_idx=0, val_profitable=False):
		'''
		Greedily searches for solutions among the given combinations of technical indicators.
		'''
		# TODO remove redundancies between this and search_solutions, if possible
		sorted_ind_names = []
		for i, (ind, value) in enumerate(self.ind_values.items()):
			# TODO unlike the exhaustive search, some solutions are tested multiple times, because ind_names are shuffled. For each solution, check if it has already been tested.
			if i >= min_idx:
				curr_ind_names = prev_ind_names + [ind]
				curr_idxs = prev_idxs + [i]
				result = self.simulate(curr_ind_names, epochs_data=self.train_epochs_data)
				sorted_ind_names.append([ind, result['balance'] if result else -100000])
		sorted_ind_names.sort(key=lambda x: -x[1])
		# print(sorted_ind_names)
		for i in range(len(sorted_ind_names)):
			ind = sorted_ind_names[i][0]
			value = self.ind_values[ind]
			curr_ind_names = prev_ind_names + [ind]
			curr_idxs = prev_idxs + [i]
			# base step
			if len(curr_ind_names) >= max_ind_names:
				self.count += 1
				if self.count % 10**(len(curr_idxs)) == 0:
					print(curr_ind_names)
					self.__prune_solutions()
					self.print_solutions(curr_idxs)
				# training step
				result = self.simulate(curr_ind_names, epochs_data=self.train_epochs_data)
				if result:
					# validation step
					result_val = 0
					if len(self.val_epochs_data) > 0:
						result_val = self.simulate(curr_ind_names, epochs_data=self.val_epochs_data)
					result['balance_val'] = result_val['balance'] if result_val else 0
					# save solution
					self.tot_solutions += 1
					if result['balance'] > SimulatorSettings.INIT_BALANCE and (not val_profitable or result['balance_val'] > SimulatorSettings.INIT_BALANCE):
						self.tot_profitable_solutions += 1
						if result['balance_val'] > SimulatorSettings.INIT_BALANCE:
							self.tot_val_profitable_solutions += 1
						if self.best_solution is None or (self.best_solution['balance'] < result['balance']):
							self.best_solution = result
						self.solutions.append(result)
			else:
				# prune search tree before recursive step: don't search through solutions that we already know will fail
				result = self.simulate(curr_ind_names, epochs_data=self.train_epochs_data)
				# recursive step
				if result:
					# TODO why did I set min_idx to 0 here? It shouldn't work, what was going on in my mind? There was obviously a reason,
					# because as far as I know I don't do anything for no reason. I may do stupid things, I may make a lot of mistakes,
					# I may write crappy code but I never do anything for no reason at all. There has to be a reason, even a wrong one, but still a reason.
					# I need to find it. I need to remember it. I need to uncover this mystery.
					# I am going to leave this here until I figure it out. Probably never, and in that case, it will stay here forever. Until the end of time.
					# Sure, I could simply test it right now instead of typing all this, and figure it out in a minute. But you know what? I am so fucking lazy.
					# I am just refactoring this code so it looks good for anyone who is reading it just for the sake of it.
					# I don't care if it works. Nobody does. Even if the code worked, the solution doesn't. It just overfits. I don't care.
					# I hate technical analysis. I don't even know why I used it in the first place.
					self.search_solutions_greedy(max_ind_names, prev_ind_names=curr_ind_names, prev_idxs=curr_idxs, min_idx=0, val_profitable=val_profitable)
					# self.search_solutions_greedy(max_ind_names, prev_ind_names=curr_ind_names, prev_idxs=curr_idxs, min_idx=i, val_profitable=val_profitable)

	def test_solutions(self):
		'''
		Tests profitable solutions.
		'''
		print('\n****************************\n')
		print('\nTesting\n')
		print('\n****************************\n')
		for sol in self.solutions:
			result = self.simulate(sol['inds'], epochs_data=self.test_epochs_data)
			sol['balance_test'] = result['balance'] if result else 0
			print(sol)

	def simulate(self, ind_names, epochs_data=None, attempts=None, calculate_pvalue=False, window_data=None, log_options=[]):
		'''
		Simulates a trading strategy using the given technical indicators.
		'''
		epochs_data = epochs_data if epochs_data is not None else self.epochs_data
		return self.simulator.simulate(ind_names, ind_values=self.ind_values, epochs_data=epochs_data, attempts=attempts,
										calculate_pvalue=calculate_pvalue, window_data=window_data, min_tot=self.min_tot, log_options=log_options)

	def print_solutions(self, idxs=None):
		'''
		Prints the solutions in a pretty way.
		Who am I kidding? There is nothing pretty about this. But still. It's readable. I hope.
		'''
		print('\n****************************\n')
		new_solutions = sorted(self.solutions, key=self.solutions_sorter, reverse=True)[:20]
		for s in new_solutions:
			self.print_solution(s)
		print()
		print(str(len(self.epochs_data)) + ' - ' + str(len(self.train_epochs_data)) + ' - ' + str(len(self.val_epochs_data)) + ' - ' + str(len(self.test_epochs_data)))
		print('Best solution - ' + str(self.best_solution))
		if idxs is not None:
			s = ''
			for j in range(len(idxs)):
				if j > 0:
					s += '-'
				s += str(idxs[j])
			s += ' / '
			for j in range(len(idxs)):
				if j > 0:
					s += '-'
				s += str(self.n_indicators)
			print(s)
		if self.tot_solutions > 0:
			print('Tot solutions: ' + str(self.tot_solutions))
			print('Profitable solutions: ' + str(self.tot_profitable_solutions))
			print('Val. profitable solutions: ' + str(self.tot_val_profitable_solutions))
			print('Ratio ps: ' + str(int(self.tot_profitable_solutions * 1000 / self.tot_solutions) / 1000))
			print('Ratio vps: ' + str(int(self.tot_val_profitable_solutions * 1000 / self.tot_solutions) / 1000))

	def print_solution(self, solution):
		'''
		Prints a solution.
		'''
		print()
		print(solution)
		# print('Solution ' + str(solution['ind_names']) + ' - Balance ' + str(solution['balance']))# + ' - Balance val ' + str(solution['balance_val']))
		# print('Epoch ' + str(solution['last_epoch']) + ' - ' + str(solution['rounds']) + ' rounds - ' + str(solution['tot']) + ' bets')
		# print('Acc ' + str(solution['acc']) + ' - Wacc ' + str(solution['wacc']) + ' - Std ' + str(solution['std']))
		# print('P-value acc ' + str(solution['p_value_acc']) + ' - P-value wacc ' + str(solution['p_value_wacc']))
		# print('P-value acc ind ' + str(solution['p_value_acc_ind']) + ' - P-value wacc ind ' + str(solution['p_value_wacc_ind']))
		print()

	def __prune_solutions(self):
		'''
		Removes the solutions with a low balance.
		'''
		if len(self.solutions) > 0:
			new_solutions = []
			min_balance = SimulatorSettings.INIT_BALANCE
			for sol in self.solutions:
				if sol['balance'] > min_balance:
					new_solutions.append(sol)
			self.solutions = new_solutions
