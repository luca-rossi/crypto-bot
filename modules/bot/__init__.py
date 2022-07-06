import time
import traceback
from win10toast import ToastNotifier
import win32api
from modules.bot.tx_handler import TxHandler
from modules.blockchain.contract import Contract
from modules.blockchain.crawler import Crawler
from modules.data.ta_logger import TALogger
from modules.strategies.strategy import Strategy
from modules.strategies.window import Window
from modules.bot.bot_data import BotData
from modules.bot.round_data import RoundData
from modules.strategies.strategy_ta import StrategyTA
from utils.const import BotLogOptions, Transactions
from utils.config import Blockchain, BotStrategy
from utils.logger import Logger
from utils.utils import Utils

class BotRunner:
	'''
	This class is called in the main file and is responsible for the bot's logic. It loops through the rounds and calls the methods for each round.
	It also handles the bot's modes: init, chill, and focus.
	- During init mode, the bot loads the datasets and initializes the new round, then switches to the chill mode.
	- During chill mode, the bot waits for the remaining time to be less than the focus time, meanwhile it checks for new transactions for the strategy.
	- During focus mode, the bot generates the predictions for the current round and, if there is enough time, attempts the transaction.
	'''
	contract = None
	crawler = None
	window = None
	window_data = None
	toaster = None
	tx_handler = None
	ta_logger = None
	bot_data = None
	round_data = None
	paused = False
	epoch = None
	bot_params = None

	def __init__(self, bot_params, window_data=None, window_init=None):
		'''
		Sets the bot parameters, loads the datasets, load the handlers, and initializes the first round.
		'''
		self.bot_params = bot_params
		self.toaster = ToastNotifier()
		print('Loading contract...')
		self.contract = Contract()
		self.crawler = Crawler(contract=self.contract)
		print('Loading window handler...')
		self.window_data = window_data
		self.window = Window(window_data)
		self.fee = Blockchain.MIN_GAS_PRICE
		print('Retrieving epoch...')
		self.__update_epoch()
		print('Loading window from simulator...')
		window_log = self.window.load(self.epoch, self.contract, window_init)
		print(window_log)
		print('Updating window with latest epochs...')
		self.window.update_window(self.epoch)
		print('Loading data handlers...')
		self.tx_handler = TxHandler(self.contract)
		self.ta_logger = TALogger()
		self.bot_data = BotData()
		self.round_data = RoundData()

	def run(self):
		'''
		Runs the main loop bot. Every iteration goes through the following steps:
		- Init mode: loads datasets, initializes new round.
		- Chill mode: checks for new transactions until the remaining time is lower than the focus time.
		- Focus mode: generates a prediction for the current round and maybe attempts a transaction.
		'''
		# TODO choose a better word for "mode"
		first = True
		while True:
			try:
				self.log('***** Starting new round *****')
				self.mode_init(first)
				first = False
				while self.round_data.is_chill_time():
					self.mode_chill()
				self.mode_focus()
				# TODO consider adding closing mode (e.g. save stuff...), maybe to replace the init mode
			except Exception as e:
				try:
					self.refresh()
					self.log('Something bad happened: ' + str(e))
					print(traceback.format_exc())
				except Exception as e1:
					time.sleep(BotStrategy.SLEEP_TIME)
					self.log('Waiting for connection...')

	def mode_init(self, first=False):
		'''
		Initializes the bot for the next round: loads the datasets and resets the round data.
		'''
		# make sure you wait until next round so you don't get back to focus mode right away
		if self.round_data and self.round_data.is_focus_time():
			self.__sleep_until_round(0, slack=True)
		# reset round
		self.round_data = RoundData()
		if not first:
			self.__mode_init_update()
		# when not in SILENT_MODE, load new epochs and transactions for up-to-date asshole detection
		if self.bot_params.silent_mode and self.tx_handler.loaded():
			self.log('Not loading new transactions in silent mode')
		else:
			self.log('Loading new epochs and transactions...')
			self.tx_handler.load()
		# silent mode
		if self.bot_params.silent_mode and self.bot_data.tx_limit_reached():
			if BotStrategy.SILENT_MODE_KILL:
				exit(0)
			else:
				# sound alarm (ironic, in silent mode...)
				for i in range(20):
					win32api.Beep(400, 2000)

	def __mode_init_update(self):
		'''
		Updates the bot's data for rounds after the first one: saves data from the previous round and checks the results if a transaction was made.
		'''
		# save tradingview predictions in inds mode
		if self.bot_params.ta_mode:
			self.log('Saving tradingview predictions...')
			self.ta_logger.save_predictions_to_file(self.epoch)
		# wait for result
		self.log('Waiting for updated epoch data...')
		# we haven't updated epoch since last one: this is 2 epochs ago
		last_epoch = self.epoch - 1
		# wait for result from contract. It is not immediate, so we need to make multiple attempts.
		for _ in range(BotStrategy.UPDATE_ATTEMPTS):
			last_epoch_data = self.contract.load_epoch(last_epoch)
			# check if last round was won
			lock_price = last_epoch_data[4]
			close_price = last_epoch_data[5]
			# close_price is 0 by default, if it's different, it means that it has been updated, so we break the loop
			if close_price != 0:
				break
			time.sleep(1)
		result = Transactions.BET_BULL if close_price > lock_price else (Transactions.BET_BEAR if close_price < lock_price else None)
		self.log('...')
		self.log('Epoch ' + str(last_epoch))
		self.log('Result ' + str(result) + ' - Bet ' + str(self.bot_data.get_prev_bet()))
		self.log('Close price: ' + str(close_price) + ' - Lock price: ' + str(lock_price))
		# update bot data with result
		logs = self.bot_data.update_bot_data(result, last_epoch, close_price)
		self.log(logs)
		# update windows
		self.window.add_bet(self.bot_data.get_prev_bet(), result, last_epoch)
		self.bot_data.update_last_bets()
		# claim rewards
		if self.bot_data.claimable_limit_reached():
			self.log('Claiming previous rounds...')
			if self.attempt_transaction(Transactions.CLAIM, epochs=self.bot_data.get_claimable_bets()):
				self.bot_data.reset_claimable_bets()

	def mode_chill(self):
		'''
		Waits for the remaining time to be lower than the focus time. Meanwhile, checks for new transactions from other players and detects assholes.
		'''
		# we update the window when the round changes
		if self.epoch != self.__update_epoch():
			self.window.update_window(self.epoch)
		# check if the contract is paused and if so, return and wait until it is resumed
		self.paused = self.contract.is_paused()
		if self.paused:
			self.log('Oh no, paused!')
			time.sleep(BotStrategy.SLEEP_TIME)
			return
		# sleep to avoid too many API calls (we only sleep when there are not many transactions)
		if not self.round_data.is_rush_time():
			time.sleep(BotStrategy.SLEEP_TIME)
		# update round data
		epoch_data = self.contract.load_epoch(self.epoch)
		start_time = epoch_data[1]
		self.round_data.update_end_round_timestamp(start_time)
		# detect txs and log round data
		round_log = str(self.bot_data.get_loss_streak()) + ' loss streak - '
		round_log += str(self.bot_data.get_tx_count()) + ' bot txs'
		if self.bot_params.detect_txs:
			self.__mode_chill_detect_txs(start_time)
			round_log += ' - ' + str(len(list(self.round_data.txs.values()))) + ' R txs' + ' - '
			round_log += 'Whales: ' + str(list(self.round_data.whales.values())) + ' - '
			round_log += 'Assholes: ' + str(self.round_data.sit_round)
		self.log(round_log)

	def __mode_chill_detect_txs(self, start_time):
		'''
		Detects new transactions and updates the round data.
		'''
		# get all entries if there are no previously detected txs, otherwise get new entries
		all_from_round = not self.round_data.txs
		if all_from_round:
			self.log('Detecting txs...')
		assholes_detected, log = self.tx_handler.detect_txs(self.round_data, self.bot_params, start_time=start_time, all_from_round=all_from_round)
		if log:
			self.log(log)
		self.round_data.sit_round = self.round_data.sit_round or assholes_detected

	def mode_focus(self):
		'''
		Uses the current strategy to predict the next bet and attempts the transaction, if possible.
		'''
		self.log('Whales detected: ' + str(list(self.round_data.whales.values())))
		self.log('Retrieving data for gap evaluation...')
		epoch_data = self.contract.load_epoch(self.epoch)
		self.log('Ready for tx stuff')
		whales_tot = sum(self.round_data.whales.values())
		# get amounts
		bull_amount = Utils.normalize_amount(epoch_data[9])
		bear_amount = Utils.normalize_amount(epoch_data[10])
		gap = (bull_amount - bear_amount)
		volume = bull_amount + bear_amount
		# get bet value
		# TODO you can use both strategies together (include TA check in Strategy)
		if self.bot_params.ta_mode:
			self.log('Retrieving tradingview predictions...')
			bet_type, analysis = StrategyTA.get_ta_bet()
			self.ta_logger.update_analysis(analysis)
			self.window.update_window(self.epoch)
			if bet_type is None:
				self.log('Ignoring tradingview prediction: ' + str(analysis['5m'].summary))
				return
			else:
				self.log('The transaction type is ' + str(bet_type))
				self.log('Attempting tradingview prediction: ' + str(analysis['5m'].summary))
		else:
			bet_type, error_log = Strategy.get_bot_bet(self.bot_params, sit_round=self.round_data.sit_round, whales_tot=whales_tot, volume=volume, gap=gap,
				vote_diff=self.round_data.get_vote_diff(),
				vote_ratio=self.round_data.get_vote_ratio(),
				remaining_time=self.round_data.get_remaining_time(),
				loss_streak_limit=self.bot_data.loss_streak_limit_reached(),
				transaction_mode=self.bot_params.transaction_mode)
		# attempt bet
		if self.paused:
			self.log('Skipping, paused!')
		else:
			if error_log is not None:
				self.log(error_log)
			if bet_type is not None:
				self.log('Prediction: ' + str(bet_type))
				# update the bet for the window, no matter what
				self.bot_data.update_curr_bet(bet_type)
				if error_log is None:
					self.log('Attempting the transaction...')
					receipt = self.attempt_transaction(bet_type)
					success = len(receipt['logs']) > 0
					self.bot_data.update_fee(success)
					if success:
						self.log('Transaction succeeded - New fee: ' + str(self.fee) + ' - Fee countdown: ' + str(self.fee_countdown))
						if not self.bot_params.silent_mode:
							self.toaster.show_toast('Transaction attempted', 'Success', duration=5)
						self.bot_data.increment_tx_count()
					else:
						self.log('Transaction failed - New fee: ' + str(self.fee) + ' - Fee countdown: ' + str(self.fee_countdown))
						if not self.bot_params.silent_mode:
							self.toaster.show_toast('Transaction attempted', 'Fail', duration=5)
		# log round summary
		self.log('*********** ROUND TXS ***********')
		self.log(self.round_data.tx_log)
		log = '\n*********** ROUND SUMMARY ***********'
		log += '\nIgnore round: ' + str(self.round_data.sit_round)
		log += '\nWhales: ' + str(list(self.round_data.whales.values()))
		log += '\nWhales tot: ' + str(whales_tot)
		log += '\nBull amount: ' + str(bull_amount)
		log += '\nBear amount: ' + str(bear_amount)
		log += '\nGap: ' + str(gap)
		log += '\nVote diff: ' + str(self.round_data.get_vote_diff())
		log += '\nBet type: ' + str(bet_type)
		log += '\n************************************'
		self.log(log, BotLogOptions.SAVE_EAGER)

	def attempt_transaction(self, bet_type, epochs=None):
		'''
		Attempts to execute a transaction and logs the result.
		'''
		tx = None
		if bet_type == Transactions.CLAIM:
			tx = self.contract.execute_transaction_claim(epochs)
		else:
			tx = self.contract.execute_transaction_bet(bet_type, BotStrategy.BET_AMOUNT, self.epoch, self.fee if self.bot_params.dynamic_fee else Blockchain.MIN_GAS_PRICE)
		self.log('Signing')
		signed_tx = self.contract.sign_transaction(tx)
		self.log('Sending')
		self.contract.send_transaction(signed_tx)
		self.log('Sent')
		receipt = self.contract.get_transaction_receipt(signed_tx)
		self.log(f'{receipt}')
		return receipt

	def refresh(self):
		'''
		Refreshes the contract query, called when something goes wrong.
		'''
		self.contract.refresh()

	def log(self, logs, log_mode=BotLogOptions.SAVE_LAZY):
		'''
		Logs the bot's actions to console and to the log file.
		'''
		Logger.log(logs, epoch=self.epoch, remaining_time=self.round_data.get_remaining_time(), log_mode=log_mode)

	def __update_epoch(self):
		'''
		Updates the current epoch by loading it from the contract.
		'''
		self.epoch = self.contract.load_current_epoch()
		return self.epoch

	def __sleep_until_round(self, seconds, slack=False):
		'''
		After everything is done in focus mode, sleeps until the next round.
		'''
		if self.round_data.is_focus_time():
			time_to_sleep = self.round_data.get_time_to_sleep(seconds)
			if slack:
				time_to_sleep += BotStrategy.SLACK_TIME
			self.log('Let\'s sleep for ' + str(time_to_sleep) + ' seconds... zzz...')
			time.sleep(time_to_sleep)
