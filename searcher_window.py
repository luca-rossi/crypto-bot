'''
Searches the best combination of window parameters for a given strategy (list of technical indicators).
This is not meant to be used to find a working solution, unless you don't mind overfitting.
'''
# TODO move content in Searcher class
from modules.data import DataLoader
from modules.data.data_processor import DataProcessor
from modules.simulator.searcher import Searcher
from utils.config import SimulatorSettings

STRATEGY_INDS = ['rev_CCI_5m', 'SMA30_15m', 'ignore_bs_STOCH.K_1m']

# TODO these possible values will be defined in WindowParams
min_payout_accuracies = [0.2, 0.3, 0.4, 0.5]
payout_windows = [5, 10, 20, 30, 40, 50]
min_window_accuracies = [-5, -0.5, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5]
bet_win_window_weights = [0, 1, 2, 4, 8, 16]
bet_loss_window_weights = [0, 1, 2, 4, 8, 16]
window_smoothings = [1, 2, 4, 8, 16]
my_windows = [5, 10, 20, 30, 40, 50]

data_loader = DataLoader()
data_processor = DataProcessor()
epochs_data, indicators = data_processor.get_processed_data(data_loader, min_epoch=SimulatorSettings.MIN_EPOCH)
print(indicators.keys())
simulator = Searcher(indicators, min_balance_ratio=-1000)
best_result = None
best_window_data = None
solutions = []
# TODO soooooooo ugly. Generalize this. Also, it would be better to use a random-greedy exploration given the combinatorial explosion
for min_payout_accuracy in min_payout_accuracies:
	for payout_window in payout_windows:
		for min_window_accuracy in min_window_accuracies:
			for bet_win_window_weight in bet_win_window_weights:
				for bet_loss_window_weight in bet_loss_window_weights:
					for window_smoothing in window_smoothings:
						for my_window in my_windows:
							if my_window > window_smoothing:
								window_data = {
									'min_payout_accuracy': min_payout_accuracy,
									'payout_window': payout_window,
									'min_window_accuracy': min_window_accuracy,
									'bet_win_window_weight': bet_win_window_weight,
									'bet_loss_window_weight': bet_loss_window_weight,
									'window_smoothing': window_smoothing,
									'my_window': my_window
								}
								result = simulator.simulate(STRATEGY_INDS, epochs_data=epochs_data, window_data=window_data)
								if result:
									result['window_data'] = window_data
									solutions.append(result)
									solutions = sorted(solutions, key=lambda x: x['balance'], reverse=True)[:5]
									if best_result is None or best_result['balance'] < result['balance']:
										best_result = result
										best_window_data = window_data
					for sol in solutions:
						print(sol)
					print()
					print(window_data)
					print('\n***** BEST:\n')
					print(best_result)
					print(best_window_data)
					print('\n*****************************\n\n')
