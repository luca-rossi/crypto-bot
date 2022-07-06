from utils.config import Blockchain, BotStrategy, StrategyParams

class BotData:
	'''
	Stores data for multiple rounds (e.g. streaks and windows).
	'''
	claimable_bets = []
	loss_streak = StrategyParams.INIT_LOSS_STREAK
	tx_count = 0
	prev_bet = None
	curr_bet = None
	net_losses = 0
	fee = 0
	fee_countdown = 0

	def update_bot_data(self, result, last_epoch, close_price):
		'''
		Updates the bot data based on the result of the last round.
		'''
		logs = []
		logs.append('Bets to claim: ' + str(self.get_claimable_bets()))
		if self.prev_bet_exists():
			if close_price == 0 or not result:			# not result should never happen, but just in case
				logs.append('Can\'t show results, something went wrong while loading epoch')
			elif result == self.prev_bet:
				if not self.loss_streak_limit_reached():
					self.add_claimable_bet(last_epoch)
				self.decrement_loss_streak()
				logs.append('Round ' + str(last_epoch) + ' won :)')
				self.net_losses -= 1
			else:
				self.increment_loss_streak()
				logs.append('Round ' + str(last_epoch) + ' lost :(')
				self.net_losses += 1
		logs.append('Claimable rounds: ' + str(self.get_claimable_bets()))
		# stop the bot if there are too many net losses
		if self.net_losses >= StrategyParams.MAX_NET_LOSSES:
			exit(0)
		return logs

	def get_claimable_bets(self):
		return self.claimable_bets

	def add_claimable_bet(self, bet):
		self.claimable_bets.append(bet)

	def reset_claimable_bets(self):
		self.claimable_bets = []

	def claimable_limit_reached(self):
		return len(self.claimable_bets) >= BotStrategy.N_BETS_TO_CLAIM

	def get_loss_streak(self):
		return self.loss_streak

	def increment_loss_streak(self):
		self.loss_streak += 1
		if self.loss_streak > StrategyParams.MAX_LOSS_STREAK:
			self.loss_streak = StrategyParams.MAX_LOSS_STREAK

	def decrement_loss_streak(self):
		self.loss_streak -= 1
		if self.loss_streak < 0:
			self.loss_streak = 0

	def loss_streak_limit_reached(self):
		return StrategyParams.USE_LOSS_STREAK and StrategyParams.MAX_LOSS_STREAK > 0 and self.loss_streak >= StrategyParams.MAX_LOSS_STREAK_BET

	def get_tx_count(self):
		return self.tx_count

	def increment_tx_count(self):
		self.tx_count += 1

	def tx_limit_reached(self):
		return self.tx_count >= BotStrategy.SILENT_MODE_MAX_TX

	def prev_bet_exists(self):
		return self.prev_bet is not None

	def update_last_bets(self):
		self.prev_bet = self.curr_bet
		self.curr_bet = None

	def update_curr_bet(self, bet):
		self.curr_bet = bet

	def get_prev_bet(self):
		return self.prev_bet

	def update_fee(self, success):
		if success:
			# decrease fee
			if self.fee_countdown > 0:
				self.fee_countdown -= 1
			if self.fee_countdown == 0 and self.fee >= Blockchain.MIN_GAS_PRICE + Blockchain.GWEI:
				self.fee -= Blockchain.GWEI
		else:
			# increase fee
			if self.fee < Blockchain.MAX_GAS_PRICE:
				self.fee += Blockchain.GWEI
				if self.fee_countdown == 0:
					self.fee_countdown = 1
				self.fee_countdown *= 2
