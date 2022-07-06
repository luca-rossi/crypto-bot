'''
Merges the files that have been previously split by logs_split.py.
'''
from modules.data.ta_logger import TALogger

ta_logger = TALogger()
# ta_logger.merge_files()			# commented for safety (learned it the hard way, accidentally ran this instead of logs_split.py)
