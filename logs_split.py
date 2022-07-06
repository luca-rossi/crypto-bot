'''
Splits the tradingview log into multiple files. Not necessary, but can be practical sometimes (where there are file size limitations).
'''
from modules.data.ta_logger import TALogger

ta_logger = TALogger()
ta_logger.split_files()
