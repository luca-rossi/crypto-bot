from utils.const import Const

class WindowParams:
	'''
	Handles the window parameters: default values, values to choose from during random search, current values.
	'''
	# TODO not used yet
	# default (initial) values
	default_params = {
		'min_payout_accuracy': -Const.INF,
		'max_payout_accuracy': 1,		# ignore with 1
		'min_window_accuracy': -Const.INF,
		'max_var': Const.INF,
		'bet_win_window_weight': 8,
		'bet_loss_window_weight': 4,
		'payout_smoothing': 9,
		'window_smoothing': 0,
		'payout_window': 28,			# 288: 1 day
		'var_window': 50,
		'my_window': 23,				# 288: 1 day
		'switch_mode': False
	}
	# values to choose from during randomization
	value_sets = {
		'min_payout_accuracy': [x * 0.01 for x in range(0, 90)],
		'max_payout_accuracy': [x * 0.01 for x in range(10, 101)],
		'min_window_accuracy': [-1000] + [x * 0.01 for x in range(-500, 100)],
		'max_var': [100000] + [x * 0.01 for x in range(10, 100)] + [x * 0.1 for x in range(100, 1000)],
		'bet_win_window_weight': [x for x in range(0, 100)],
		'bet_loss_window_weight': [x for x in range(0, 100)],
		'payout_smoothing': [x for x in range(0, 100)],
		'window_smoothing': [x for x in range(0, 100)],
		'payout_window': [x for x in range(1, 500)],
		'my_window': [x for x in range(1, 500)],
		'var_window': [x for x in range(1, 500)],
		'switch_mode': [False],
	}
	params = {}

	def __init__(self):
		self.params = self.default_params.copy()

	def set_params(self, randomize_none=False, reset=False, params=None):
		if reset:
			self.params = self.default_params.copy()
		if params is not None:
			for key, value in params.items():
				self.params[key] = value

	# def set_params(self, randomize_none=False, reset=True,
	# 				min_payout_accuracy=None, max_payout_accuracy=None, min_window_accuracy=None, max_var=None,
	# 				bet_win_window_weight=None, bet_loss_window_weight=None, payout_smoothing=None, window_smoothing=None,
	# 				payout_window=None, var_window=None, my_window=None, switch_mode=None):
	# 	self.min_payout_accuracy = min_payout_accuracy if min_payout_accuracy is not None else (self.min_payout_accuracy if not randomize_none else random(min_payout_accuracy))
	# 	self.max_payout_accuracy = max_payout_accuracy if max_payout_accuracy is not None else (self.max_payout_accuracy if not randomize_none else random(max_payout_accuracy))
	# 	self.min_window_accuracy = min_window_accuracy if min_window_accuracy is not None else (self.min_window_accuracy if not randomize_none else random(min_window_accuracy))
	# 	self.max_var = max_var if max_var is not None else (self.max_var if not randomize_none else random(max_var))
	# 	self.bet_win_window_weight = bet_win_window_weight if bet_win_window_weight is not None else (self.bet_win_window_weight if not randomize_none else random(bet_win_window_weight))
	# 	self.bet_loss_window_weight = bet_loss_window_weight if bet_loss_window_weight is not None else (self.bet_loss_window_weight if not randomize_none else random(bet_loss_window_weight))
	# 	self.payout_smoothing = payout_smoothing if payout_smoothing is not None else (self.payout_smoothing if not randomize_none else random(payout_smoothing))
	# 	self.window_smoothing = window_smoothing if window_smoothing is not None else (self.window_smoothing if not randomize_none else random(window_smoothing))
	# 	self.payout_window = payout_window if payout_window is not None else (self.payout_window if not randomize_none else random(payout_window))
	# 	self.var_window = var_window if var_window is not None else (self.var_window if not randomize_none else random(var_window))
	# 	self.my_window = my_window if my_window is not None else (self.my_window if not randomize_none else random(my_window))
	# 	self.switch_mode = switch_mode if switch_mode is not None else (self.switch_mode if not randomize_none else random(switch_mode))
