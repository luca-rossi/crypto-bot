'''
Searches the best combination of technical indicators and window parameters with a greedy random search.
This is not meant to be used to find a working solution, unless you don't mind overfitting.
'''
# TODO move content in Searcher class
import random
import math
from modules.data import DataLoader
from modules.data.data_processor import DataProcessor
from modules.simulator.searcher import Searcher
from utils.config import SimulatorSettings

# TODO args
CONTROL = False
MAX_INDS = 3
UPDATE_INDS = True
STD_WEIGHT = 1
WITH_WINDOW = False
B = 1.15
R = 35

# TODO these possible values will be defined in WindowParams
window_choices = {
	'min_payout_accuracy': [x * 0.01 for x in range(0, 90)],
	'max_payout_accuracy': [x * 0.01 for x in range(10, 101)],
	'min_window_accuracy': [-1000] + [x * 0.01 for x in range(-500, 100)],
	'max_var': [100000] + [x * 0.01 for x in range(10, 100)] + [x * 0.1 for x in range(100, 1000)],
	'bet_win_window_weight': [x for x in range(0, 100)],
	'bet_loss_window_weight': [x for x in range(0, 100)],
	'payout_smoothing': [x for x in range(0, 100)],
	'window_smoothing': [x for x in range(0, 100)],
	'payout_window': [x for x in range(1, 500)],
	'my_window': [x for x in range(1, 500)],
	'var_window': [x for x in range(1, 500)],
	'switch_mode': [False, True],
}

data_loader = DataLoader()
data_processor = DataProcessor()
epochs_data, indicators = data_processor.get_processed_data(data_loader, min_epoch=SimulatorSettings.MIN_EPOCH)
ind_keys = [*indicators.keys()][:]
print(ind_keys)
simulator = Searcher(indicators, control=CONTROL)
solutions = []
count_attempts = 0
count_profitable_attempts = 0
# this is more like a "greedy random" solution
# TODO check if something else here can be optimized
while True:
	if len(solutions) == 0:
		# choose indicators
		num_inds = math.floor(1 + MAX_INDS * random.random())
		strategy_inds = []
		for i in range(num_inds):
			strategy_inds.append(random.choice(ind_keys))
		# create a new solution
		window_data = {}
		for k, v in window_choices.items():
			window_data[k] = random.choice(window_choices[k])
	else:
		# pick the best solution
		strategy_inds = solutions[0]['inds'].copy()
		window_data = solutions[0]['window_data'].copy()
		if UPDATE_INDS:
			# choose a subsample of the indicators (could be zero) to keep
			n_inds_to_keep = int((len(strategy_inds) + 1) * random.random())
			strategy_inds = random.sample(strategy_inds, n_inds_to_keep)
			n_inds_to_create_max = MAX_INDS - len(strategy_inds)
			n_inds_to_create = int((n_inds_to_create_max + 1) * random.random())
			for i in range(n_inds_to_create):
				strategy_inds.append(random.choice(ind_keys))
		# choose some random parameters to change in the window (could be zero)
		if WITH_WINDOW:
			params = list(window_choices.keys())
			sample_size_new_window = int((len(params) + 1) * random.random())
			new_params = random.sample(params, sample_size_new_window)
			for p in new_params:
				window_data[p] = random.choice(window_choices[p])
	# remove the extra 'strategy' indicator
	for i in strategy_inds:
		if 'strategy' in i:
			strategy_inds.remove(i)
	window_data = None
	count_attempts += 1
	result = simulator.simulate(strategy_inds, epochs_data=epochs_data, attempts=count_attempts, calculate_pvalue=False, window_data=window_data)
	if result:
		# TODO parametrize optimization function
		# if len(solutions) == 0 or solutions[-1]['balance'] - solutions[-1]['std'] * STD_WEIGHT < result['balance'] - solutions[-1]['std'] * STD_WEIGHT:
		if len(solutions) == 0 or solutions[-1]['balance'] < result['balance']:
			result['window_data'] = window_data
			solutions.append(result)
		if result['balance'] > SimulatorSettings.INIT_BALANCE:
			count_profitable_attempts += 1
	if count_attempts % 100 == 0:
		# TODO parametrize optimization function
		# solutions = sorted(solutions, key=lambda x: 1 - x['p_value_wacc_ind'], reverse=True)[:10]
		# solutions = sorted(solutions, key=lambda x: x['balance'] - x['std'] * STD_WEIGHT, reverse=True)[:5]
		solutions = sorted(solutions, key=lambda x: x['balance'], reverse=True)[:5]
		print()
		print('***********************')
		print()
		for sol in solutions:
			simulator.print_solution(sol)
			print(sol['window_data'])
			print()
		print('Successes: ' + str(count_profitable_attempts))
		print('Tot: ' + str(count_attempts))
		print('Profitable solutions: ' + str(count_profitable_attempts / count_attempts))
