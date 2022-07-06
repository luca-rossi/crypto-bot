'''
Searches the best combination of technical indicators with an exhaustive or greedy search.
This is not meant to be used to find a working solution, unless you don't mind overfitting.
'''
import argparse
from modules.data import DataLoader
from modules.data.data_processor import DataProcessor
from modules.simulator.searcher import Searcher
from utils.config import SimulatorSettings

parser = argparse.ArgumentParser()
parser.add_argument('--num_inds', '-n', type=float, default=2, help='the number of indicators used in a solution. The higher the number, the longer the search time (exponentially), and the higher the chance of overfitting.')
parser.add_argument('--train_ratio', '-t', type=float, default=1, help='fraction of the epochs evaluated during the search to choose the best solution')
parser.add_argument('--trainval_ratio', '-v', type=float, default=1, help='fraction of the epochs evaluated during the search to choose the best solution, including the part used for validation')
parser.add_argument('--min_tot_ratio', '-m', type=float, default=0, help='minimum fraction of the epochs that needs to result in a bet for the solution to be considered')
parser.add_argument('--control', '-c', action='store_true', default=False, help='do a control experiment (every bet will be random), to estimate the chances of overfitting')
parser.add_argument('--greedy', '-a', action='store_true', default=False, help='do a greedy search instead of exhaustive')
parser.add_argument('--val_profitable', '-p', action='store_true', default=False, help='if True, solutions need to be profitable in the validation set too to be considered')
opt = parser.parse_args()

# TODO DataProcessor will be removed
data_loader = DataLoader()
data_processor = DataProcessor()
solutions_sorter = lambda x: x['balance']		# or lambda x: x['balance'] * x['balance_val']		or lambda x: 1 - x['p_value_wacc_ind']#x['p_value_acc']
epochs_data, indicators = data_processor.get_processed_data(data_loader, min_epoch=SimulatorSettings.MIN_EPOCH)
# print(indicators.keys())
searcher = Searcher(indicators, solutions_sorter=solutions_sorter, control=opt.control)		# TODO , window_data={...})
searcher.init_epochs(epochs_data, train_ratio=opt.train_ratio, trainval_ratio=opt.trainval_ratio, min_tot_ratio=opt.min_tot_ratio)
if opt.greedy:
	searcher.search_solutions_greedy(opt.num_inds, val_profitable=opt.val_profitable)
else:
	searcher.search_solutions(opt.num_inds, val_profitable=opt.val_profitable)
searcher.print_solutions()
# TODO searcher.test_solutions()
