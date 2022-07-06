'''
Runs the main bot.
'''
import argparse
from modules.data import DataLoader
from modules.data.data_processor import DataProcessor
from modules.bot import BotRunner
from modules.simulator.searcher import Searcher
from modules.strategies.strategy import Strategy
from utils.config import BotStrategy, SimulatorSettings
from utils.const import SimLogOptions

parser = argparse.ArgumentParser()
parser.add_argument('--transaction_mode', '-t', action='store_true', help='if true, transactions are actually attempted, otherwise they are just simulated')
parser.add_argument('--dynamic_fee', '-f', action='store_false', help='if true, the fee amount is increased when transactions fail (and decreased when they succeed)')
parser.add_argument('--silent_mode', '-s', action='store_false', help='if true, the bot will not load new tx data at every round (called silent because this operation caused the laptop fans to activate at night)')
parser.add_argument('--ta_mode', '-a', action='store_true', help='if true, the bot will use the strategy based on technical analysis')
parser.add_argument('--load_window', '-l', action='store_true', help='if true, the bot will run the simulator before starting, so it can get accurate window data (only to be used in TA mode, inefficient and obsolete)')
parser.add_argument('--detect_txs', '-d', action='store_false', help='if true, the bot detects other players\' transactions during chill mode')
parser = Strategy.get_params(parser)
params = parser.parse_args()
Strategy.set_params(params)
# TODO load dynamically
window_data = None#BotStrategy.WINDOW_DATA
window_init = None

if params.load_window:
	# run the simulator first to get the averages
	print('Preparing simulator...')
	data_loader = DataLoader()
	data_processor = DataProcessor()
	epochs_data, indicators = data_processor.get_processed_data(data_loader, min_epoch=SimulatorSettings.MIN_EPOCH)
	print(indicators.keys())
	print('Simulating...')
	simulator = Searcher(indicators, min_balance_ratio=-1000)
	result = simulator.simulate(BotStrategy.INDICATORS, epochs_data=epochs_data, window_data=BotStrategy.WINDOW_DATA, log_options=[SimLogOptions.SAVE_WINDOW])
	# TODO window_init = Window(result['window_data'])		... (we don't need it with augmented txs)
	print(result)
print('Starting bot...')
bot = BotRunner(params, window_data, window_init)
bot.run()
