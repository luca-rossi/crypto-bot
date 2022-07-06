'''
Makes one fast bull bet.
'''
from modules.bot import BotRunner
from utils.const import Transactions

bot = BotRunner()
try:
	bot.attempt_transaction(Transactions.BET_BULL)
except Exception as e:
	print(f'Transaction failed - {e}')
