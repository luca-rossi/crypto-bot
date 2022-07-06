import time
from utils.config import BotStrategy
from utils.const import Const

class RoundData:
	'''
	Stores all the data about a specific round. For every round, a new instance of this class is created, so initialization is easier and more intuitive.
	'''
	epoch = None
	end_round_timestamp = None
	whales = None
	txs = None
	bull_votes = None
	bear_votes = None
	sit_round = None		# if assholes are detected
	tx_log = None

	def __init__(self):
		'''
		A new instance of this class is created every time a new round starts.
		'''
		self.epoch = 0
		self.end_round_timestamp = 0
		self.whales = {}
		self.txs = {}
		self.bull_votes = 0
		self.bear_votes = 0
		self.sit_round = False
		self.tx_log = ''

	def add_tx_vote(self, address, value, bullish):
		if bullish:
			self.bull_votes += 1
			self.txs[address] = value
		else:
			self.bear_votes += 1
			self.txs[address] = -value

	def get_vote_diff(self):
		return self.bull_votes - self.bear_votes

	def get_vote_ratio(self):
		return self.bull_votes / self.bear_votes if self.bear_votes > 0 else Const.INF

	def update_end_round_timestamp(self, start_time):
		self.end_round_timestamp = start_time + Const.ROUND_DURATION

	def get_remaining_time(self):
		return int(self.end_round_timestamp - time.time()) % Const.ROUND_DURATION

	def get_time_to_sleep(self, seconds):
		return self.get_remaining_time() - seconds

	def is_init_time(self):
		return self.get_remaining_time() <= BotStrategy.MIN_TIME_FOR_TX

	def is_chill_time(self):
		return self.get_remaining_time() >= BotStrategy.FOCUS_TIME

	def is_rush_time(self):
		return self.get_remaining_time() < BotStrategy.RUSH_TIME

	def is_focus_time(self):
		return self.get_remaining_time() < BotStrategy.FOCUS_TIME
