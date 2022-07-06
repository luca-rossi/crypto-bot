'''
Builds the blacklist by calling the Crawler simulator.
Allows to choose different strategies to build the blacklist:
- Round bets: blacklist address with bets that are multiples of 5 (empirically observed).
- Accuracy: blacklist address with bets that are more than X% accurate.
- Suspicious accuracy: same as accuracy but automatically blacklist new whales (until proven "innocent").
- Graph expansion: expand the blacklist graph by one level, adding all the addresses linked to blacklisted addresses by transactions.
- Whitelist: start by blacklisting everyone, then build the whitelist.
'''
import argparse
from modules.blockchain.crawler import Crawler
from modules.strategies.strategy import Strategy

# TODO add ROUND_FORGIVENESS
ROUND_FORGIVENESS = True
parser = argparse.ArgumentParser()
parser.add_argument('--min_epoch', '-m', type=int, default=0, help='first epoch')
parser.add_argument('--max_epoch', '-M', type=int, default=1000000, help='last epoch')
parser.add_argument('--value', '-V', type=float, default=Strategy.params.min_whale_bet, help='min absolute value of the txs to consider')
parser.add_argument('--acc', 'A', type=float, default=1, help='min accuracy for the whales to blacklist')
parser.add_argument('--count', '-c', type=float, default=10, help='min number of txs from a whale for forgiveness evaluation')
parser.add_argument('--strategy_rounds', '-r', action='store_true', default=False, help='build blacklist from round bets')
parser.add_argument('--strategy_acc', '-a', action='store_true', default=False, help='build blacklist from accuracies')
parser.add_argument('--strategy_sus', '-s', action='store_true', default=False, help='ignore any whale\'s first tx')
parser.add_argument('--strategy_graph', '-g', action='store_true', default=False, help='build blacklist by expanding tx graph')
parser.add_argument('--strategy_whitelist', '-w', action='store_true', default=False, help='start by blacklisting everyone, then build the whitelist')
parser.add_argument('--log_every', '-l', type=int, default=50, help='number of epochs between logs')
parser.add_argument('--verbose', '-v', action='store_true', default=False, help='log every epoch')
args = parser.parse_args()

if not args.strategy_rounds and not args.strategy_acc and not args.strategy_graph and not args.strategy_whitelist:
	print('Choose at least one strategy')
	exit(0)
crawler = Crawler()
crawler.simulate_realtime_blacklist(args.min, args.max, args.value, args.acc, args.count, ROUND_FORGIVENESS,
									args.strategy_rounds, args.strategy_acc, args.strategy_sus, args.strategy_graph, args.strategy_whitelist,
									args.log_every, args.verbose)
