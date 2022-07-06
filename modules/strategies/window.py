class Window:
	'''
	Handles the operations on a window with information about the latest N epochs.
	'''
	N_EPOCHS_TO_SHIFT = 2		# TODO param
	contract = None
	window_data = None
	avg_payout_accuracy = None
	avg_window_accuracy = None
	last_updated_epoch = 0		# the last window update epoch
	last_bet_weight = 0.5

	def __init__(self, window_data):
		self.window_data = window_data

	def load(self, curr_epoch, contract, window_init):
		'''
		Initializes and loads the window parameters.
		'''
		window_init = window_init or {
			'last_updated_epoch': curr_epoch - 3,
			'avg_payout_accuracy': 0.5,
			'avg_window_accuracy': 0.5
		}
		self.contract = contract
		self.last_updated_epoch = window_init['last_updated_epoch']
		self.avg_payout_accuracy = window_init['avg_payout_accuracy']
		self.avg_window_accuracy = window_init['avg_window_accuracy']
		return str(self.last_updated_epoch) + ' ' + str(self.avg_payout_accuracy) + ' ' + str(self.avg_window_accuracy)

	def set_window_data(self, window_data):
		self.window_data = window_data

	def add_bet(self, bet, result, epoch):
		'''
		Adds the latest bet to the window.
		'''
		if not self.window_data:
			return
		bet_weight = 0.5
		if bet is None:
			bet_weight = 0.5
		elif bet == result:
			bet_weight = 1 + self.window_data['bet_win_window_weight']
		else:
			bet_weight = -self.window_data['bet_loss_window_weight']
		self.last_bet_weight = bet_weight

	def update_window(self, curr_epoch):
		'''
		Updates the window with the latest epoch data.
		'''
		if not self.window_data:
			return
		# TODO if last_updated_epoch < last_added_epoch
		if self.last_updated_epoch < curr_epoch - self.N_EPOCHS_TO_SHIFT:
			loaded_epoch = self.last_updated_epoch
			new_payout_win = 0.5
			new_my_win = self.last_bet_weight
			# 2 epochs lag
			for loaded_epoch in range(loaded_epoch + 1, curr_epoch + 1 - self.N_EPOCHS_TO_SHIFT):
				# load last epoch (even after loading all, so we include the latest epoch that hasn't been updated)
				print('Updating window with last epoch...')
				epoch_data = self.contract.load_epoch(loaded_epoch)
				new_payout_win = self.get_payout_outcome_from_epoch_data(epoch_data)
				self.avg_payout_accuracy, self.avg_window_accuracy = self.__update_window_averages(self.avg_payout_accuracy, self.avg_window_accuracy, new_payout_win, new_my_win)
				print(loaded_epoch)
				print(self.avg_payout_accuracy)
				print(self.avg_window_accuracy)
			self.last_updated_epoch = loaded_epoch

	def check_averages(self):
		'''
		Checks if the window parameters lie within acceptable ranges.
		'''
		return self.avg_payout_accuracy >= self.window_data['min_payout_accuracy'] and self.avg_payout_accuracy <= self.window_data['max_payout_accuracy'] and self.avg_window_accuracy >= self.window_data['min_window_accuracy']

	def get_payout_outcome_from_epoch_data(self, epoch_data):
		'''
		Returns the payout outcome from the epoch data: 1 if the crowd was correct, 0 if the crowd was wrong, and 0.5 in the case of a draw.
		'''
		lock_price = epoch_data[4]
		close_price = epoch_data[5]
		bull_amount = epoch_data[9]
		bear_amount = epoch_data[10]
		if bull_amount > 0 and bear_amount > 0:
			bull_bear_ratio = bull_amount / bear_amount
			bear_payout = 1 + bull_bear_ratio
			bull_payout = 1 + 1 / bull_bear_ratio
			payout = 0
			if close_price < lock_price:
				payout = bear_payout
			elif close_price > lock_price:
				payout = bull_payout
			return 1 if payout > 0 and payout < 2 else 0
		return 0.5

	def __update_window_averages(self, avg_payout_accuracy, avg_window_accuracy, new_payout_win, new_my_win):
		'''
		Updates the window averages with the latest epoch data. Uses standard or exponential averages.
		'''
		payout_window = self.window_data['payout_window']
		my_window = self.window_data['my_window']
		# if smoothing is 0, use standard average, otherwise use exponential one
		if avg_payout_accuracy is None:
			avg_payout_accuracy = 0.5#new_payout_win
		else:
			if self.window_data['payout_smoothing'] == 0:
				avg_payout_accuracy = avg_payout_accuracy + (new_payout_win - avg_payout_accuracy) / payout_window
			else:
				avg_payout_accuracy = new_payout_win * self.window_data['payout_smoothing'] / (1 + payout_window) + avg_payout_accuracy * (1 - self.window_data['payout_smoothing'] / (1 + payout_window))
		if avg_window_accuracy is None:
			avg_window_accuracy = 0.5#new_my_win
		else:
			if self.window_data['window_smoothing'] == 0:
				avg_window_accuracy = avg_window_accuracy + (new_my_win - avg_window_accuracy) / my_window
			else:
				avg_window_accuracy = new_my_win * self.window_data['window_smoothing'] / (1 + my_window) + avg_window_accuracy * (1 - self.window_data['window_smoothing'] / (1 + my_window))
		return avg_payout_accuracy, avg_window_accuracy
