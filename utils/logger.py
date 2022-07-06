import time
from utils.config import Files
from utils.const import BotLogOptions

class Logger:
	'''
	Static class that logs the bot operations. It has two modes: lazy or eager. If lazy, it stores the logs in a string to be saved later. If eager, it saves the logs immediately.
	'''
	to_log = ''

	def log(logs, epoch=0, remaining_time=0, log_mode=BotLogOptions.SAVE_LAZY):
		if not isinstance(logs, list):
			logs = [logs]
		for log in logs:
			log_str = str(time.ctime()) + ' - R ' + str(epoch) + ' - ' + str(remaining_time) + 's left - ' + log
			print(log_str)
			log_str += '\n'
			save = False
			if log_mode == BotLogOptions.CONSOLE:
				# check if there is a log to save
				if Logger.to_log != '':
					save = True
			else:
				# store the log in a string to be saved later (if lazy) or just in case there is an exception (if eager)
				Logger.to_log += log_str
				if log_mode == BotLogOptions.SAVE_EAGER:
					# save log now
					save = True
			if save:
				with open(Files.LOG_BOT, 'a') as f:
					f.write(Logger.to_log)
				Logger.to_log = ''
