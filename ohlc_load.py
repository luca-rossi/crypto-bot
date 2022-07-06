'''
Loads and visualizes a Binance OHLC dataset for experiments.
'''
import argparse
from modules.data.binance_loader import BinanceLoader
from utils.config import Files

parser = argparse.ArgumentParser()
parser.add_argument('--filename', '-f', type=str, default=Files.DATA_BINANCE_OHLC_1M, help='path of the csv file where to load and/or save the data')
parser.add_argument('--symbol', '-s', type=str, default='BNBUSDT', help='symbol of the pair to load')
parser.add_argument('--candle', '-c', type=str, default='1m', help='size of the candle')
parser.add_argument('--remote', '-r', action='store_true', help='if true, load data remotely, otherwise from file')
args = parser.parse_args()

remote_loader = BinanceLoader()
df = remote_loader.load(args.filename, symbol=args.symbol, candle=args.candle, remote=args.remote)
print(df)
