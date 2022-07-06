'''
Runs the simulator. The strategy parameters are defined here.
'''
import argparse
from modules.data import DataLoader
from modules.data.data_processor import DataProcessor
from modules.simulator.searcher import Searcher
from utils.const import SimLogOptions
from modules.strategies.strategy import Strategy

LOG_OPTIONS = [SimLogOptions.MINIMAL, SimLogOptions.EPOCHS]
STRATEGY_INDS = ['strategy_5m']					# remember to add _5m to strategies as well. TODO I know, it's ugly, I will fix it later. Probably.
WINDOW_DATA = {
	'min_payout_accuracy': -1000,
	'max_payout_accuracy': 1,
	'payout_smoothing': 1,
	'payout_window': 20,
	'min_window_accuracy': -1000,
	'my_window': 100,
	'bet_win_window_weight': 0,
	'bet_loss_window_weight': 0,
	'window_smoothing': 1,
	'max_var': 100000,
	'var_window': 3,
	'switch_mode': False
}

parser = argparse.ArgumentParser()
parser = Strategy.get_params(parser)
params = parser.parse_args()
Strategy.set_params(params)

data_loader = DataLoader()
data_processor = DataProcessor()
epochs_data, indicators = data_processor.get_processed_data(data_loader, min_epoch=params.min_epoch)
# TODO do we really need Searcher here?
simulator = Searcher(indicators, min_balance_ratio=-1000)
simulator.simulate(STRATEGY_INDS, epochs_data=epochs_data, window_data=WINDOW_DATA, log_options=LOG_OPTIONS)
