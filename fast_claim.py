'''
Claims the reward of a given epoch.
'''
import argparse
from modules.bot import BotRunner
from utils.const import Transactions

parser = argparse.ArgumentParser()
parser.add_argument('--epoch', '-e', type=int, default=None, help='epoch to claim')
args = parser.parse_args()

try:
	if not args.epoch:
		raise Exception('Please specify an epoch')
	bot = BotRunner()
	bot.attempt_transaction(Transactions.CLAIM, [args.epoch])
except Exception as e:
	print(f'Transaction failed - {e}')
