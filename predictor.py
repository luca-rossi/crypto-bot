'''
Strategy based on deep neural networks.
Two types of input datasets: epochs or OHLCV (Binance) data.
Two types of output: prediction (bull or bear) or close price.
'''
# TODO check if it still works
import argparse
from keras.models import load_model
from modules.predictor import Predictor
from utils.config import Files

parser = argparse.ArgumentParser()
parser.add_argument('--train_split', '-s', type=float, default=0.7, help='fraction of data to use for training')
parser.add_argument('--val_split', '-v', type=float, default=0.25, help='fraction of data to use for validation')
parser.add_argument('--epochs', '-e', type=int, default=50, help='number of epochs to train')
parser.add_argument('--batch_size', '-b', type=int, default=32, help='batch size')
parser.add_argument('--conf', '-c', type=float, default=0.6, help='minimum confidence required to consider a prediction')
parser.add_argument('--eval', '-E', action='store_true', help='just evaluate the model on the saved preprocessed dataset')
args = parser.parse_args()

if args.eval:
	predictor = Predictor(Files.DATA_PREP, col_features=2, col_after_features=-3, col_target=-2, col_payout=-3)
	model = load_model(Files.MODEL)
else:
	predictor = Predictor(Files.DATA_BINANCE_OHLC_1M, is_ohlcv=True, col_after_features=6)
	model = predictor.build_model_cls()
	model = predictor.train_model(epochs=args.epochs, batch_size=args.batch_size, validation_split=args.val_split, load=False, save=True)
predictor.evaluate(conf=args.conf)
