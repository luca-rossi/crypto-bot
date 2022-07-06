'''
Visualizes the transaction history (from all users) filtered by some parameters, e.g. min and max epoch, min value, etc.
'''
# TODO move content in data module
# TODO fix (remains stuck while cleaning txs)
# TODO implement remote mode (load txs from API instead of file)
import argparse
import pandas as pd
from modules.blockchain.contract import Contract
from modules.data import DataLoader
from modules.data.data_processor import DataProcessor
from modules.strategies.strategy import Strategy
from utils.const import Const, Transactions

# TODO param max time
parser = argparse.ArgumentParser()
parser.add_argument('--min_whale_bet', '-w', type=float, default=5, help='min absolute value of a tx to be considered a whale bet')
parser.add_argument('--value', '-val', type=float, default=0, help='min absolute value of the txs to show')
parser.add_argument('--time', '-t', type=float, default=Const.ROUND_DURATION, help='max round time of the txs to show (from 0 to 300)')
parser.add_argument('--from', '-f', dest='address', type=str, default=None, help='specific address to show (if specified)')
parser.add_argument('--only_epoch', '-o', action='store_true', help='consider just the min epoch')
parser.add_argument('--addresses', '-a', action='store_true', help='group txs by address')
parser.add_argument('--epochs', '-e', action='store_true', help='group txs by epoch')
parser = Strategy.get_params(parser)
args = parser.parse_args()
Strategy.set_params(args)

if args.addresses and args.epochs:
	print('Can\'t group by both addresses and epochs, no grouping will be applied')
	args.addresses = False
	args.epochs = False
contract = Contract()
data_loader = DataLoader()
data_processor = DataProcessor()
df_ep, df = data_loader.load(update=False)
df = data_processor.augment_txs_with_accuracy(df, df_ep, args.min_whale_bet)
filter_epochs = (df['epoch'] == args.min_epoch) if args.only_epoch else ((df['epoch'] >= args.min_epoch) & (df['epoch'] <= args.max_epoch))
txs = df[filter_epochs & (df['value'] >= args.value)]
if args.address:
	txs = txs[df['from'] == args.address]
else:
	txs = txs.drop(['count', 'accuracy', 'w_count', 'w_accuracy'], axis=1)
if args.only_epoch:
	txs['pay_bull'] = txs.loc[txs['input'] == Transactions.BET_BULL, 'value'].cumsum()
	txs['pay_bear'] = txs.loc[txs['input'] == Transactions.BET_BEAR, 'value'].cumsum()
	txs.loc[txs['input'] == Transactions.BET_BULL, 'vote_bull'] = 1
	txs.loc[txs['input'] == Transactions.BET_BEAR, 'vote_bear'] = 1
	txs['votes_bull'] = txs.loc[txs['input'] == Transactions.BET_BULL, 'vote_bull'].cumsum()
	txs['votes_bear'] = txs.loc[txs['input'] == Transactions.BET_BEAR, 'vote_bear'].cumsum()
	txs = txs.drop(['vote_bull', 'vote_bear'], axis=1)
if args.epochs:
	group_txs = pd.DataFrame()
	group_txs['tot_value'] = txs.groupby('epoch').sum()['value']
	group_txs['biggest_whale'] = txs.groupby('epoch').agg({'value': 'max', 'from': 'min'})['from']
	txs = group_txs
if args.addresses:
	group_txs = pd.DataFrame()
	group_txs['count'] = txs.groupby('from').count()['value']
	group_txs['sum'] = txs.groupby('from').sum()['value']
	group_txs['avg_value'] = group_txs['sum'] / group_txs['count']
	group_txs['avg_time'] = txs.groupby('from').mean()['time'].astype(int)
	# TODO include accuracy
	txs = group_txs
print(txs.to_string())
