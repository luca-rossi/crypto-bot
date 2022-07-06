# Bot for crypto prediction markets

**DISCLAIMER: THE CONTENT OF THIS REPOSITORY IS FOR EDUCATIONAL PURPOSES ONLY. SOME OF THESE STRATEGIES USED TO WORK BUT NO LONGER DO (NO STRATEGY WORKS FOREVER). IF YOU USE THIS BOT YOU WILL LOSE MONEY. YOU HAVE BEEN WARNED.**

This is a bot that plays on the PancakeSwap Prediction dApp (but it could potentially be generalized to similar decentralized prediction markets as well). It started as a weekend project and then I spent months on it just to end up with the big mess you see here. I finally found a strategy that worked and *didn't* overfit, until it stopped being profitable, so I realized that I should probably do something more productive with my time...

## Usage

Create the file `utils/config.py` before running (you can copy it from `utils/config.example`, remember to fill the blockchain data). The logic of the bot is in the `modules/` folder. All the top-level files are standalone runnable scripts.

- `main.py` - Runs the main bot.
- `simulator.py` - Runs the simulator.
- `searcher.py` - Among a list of technical indicators, simulates various combinations (using greedy or exhaustive techniques) to find the optimal one.
- `searcher_random.py` - Like `searcher.py`, it simulates various combinations, but it performs a greedy search selecting random indicators and parameters for each simulation.
- `searcher_window.py` - Like `searcher.py`, it simulates various combinations, but it iterates different window parameters rather than technical indicators.
- `fast_bet_bear.py` - Places a bear bet. Useful when you want to bet manually but don't want to use the (slow) PancakeSwap interface.
- `fast_bet_bull.py` - Places a bull bet. Useful when you want to bet manually but don't want to use the (slow) PancakeSwap interface.
- `fast_claim.py` - Claims a previously won round.
- `logs_split.py` - Splits the saved TradingView log into multiple files. It can be practical where there are file size limitations.
- `logs_merge.py` - Merges the files previously split by `logs_split.py`.
- `ohlc_load.py` - Loads and visualizes a Binance OHLC dataset.
- `ohlc_ta.py` - Creates a dataset of technical indicators from a Binance OHLC dataset.
- `ohlc_ta_strategy_value.py` - From a Binance OHLC dataset with technical indicators, simulates bets based on the value of those indicators.
- `ohlc_ta_strategy_signal.py` - From a Binance OHLC dataset with technical indicators, simulates bets based on signals generated from those indicators.
- `predictor.py` - Runs strategy based on deep neural networks.
- `predictor_ml.py` - Runs strategy based on machine learning models.
- `predictor_lstm.py` - Runs strategy based on deep (LSTM) neural networks.
- `predictor_window.py` - Runs strategy based on deep (LSTM) neural networks (alternative implementation).
- `predictor_dqn.py` - Runs strategy based on reinforcement learning (DQN).
- `tx_show.py` - Visualizes the transaction history (from all users) filtered by some parameters.
- `tx_build_blacklist.py` - Builds the blacklist by detecting assholes with various methods.
- `tx_expand_blacklist.py` - Expands the blacklist graph by including all the addresses linked by transactions (except smart contracts).

When you run the bot or the simulator for the first time, you will need to wait some time (a few hours) to load the data (past epochs and transactions). Loading data directly from the blockchain can be slow and messy. If you notice that the loader remains stuck trying to load the same epoch over and over again, you will need to restart the script and manually change the starting epoch (e.g. 1000 epochs later). I will probably fix this at some point.

Do not the run bot and the simulator (or multiple simulations) at the same time, you risk overriding and losing the transactions.

There are currently some issues with loading transactions for the cakeusd pair (bnbusd works just fine). I'm working on fixing those issues.

## How it works

### PancakeSwap Prediction and the bot

PancakeSwap Prediction is a decentralized app that allows players to bet on whether the price of BNB will rise or fall in the next 5-minute round. The players who are correct in their predictions are rewarded accordingly to the payout. Since the prize pool is split among the winners, the fewer the bets on the winning position, the higher the payout.

[Link to the dApp](https://pancakeswap.finance/prediction)

[Link to the docs](https://docs.pancakeswap.finance/products/prediction)

The goal of this bot is to use strategies based on statistics to produce profits in a regular way.

The bot automatically evaluates whether to bet in a given round and which position. Different strategies have been implemented (summarized later).

Although this bot is optimized for the PancakeSwap Prediction dApp, it can be generalized to any similar dApp.

The bot has 3 modes:

- Init mode - A new round starts and round data is initialized (everything from the previous round, e.g. transactions, is reset).
- Chill mode - While waiting for the end of the round, transactions are detected (for strategies based on expected value). Called "chill mode" because there is no rush, the bot just goes through a loop in which it sleeps for some time and detects new transactions.
- Focus mode - A few seconds before the end of the round, a choice needs to be made (whether to make a transaction and which one) based on the available data (e.g. technical indicators or transactions). Called "focus mode" because it needs to be optimized to be executed fast (late enough to gather more data, early enough to be able to complete a transaction).

The simulator uses all the past epochs and user transactions on the dApp (yes, all the transactions) to simulate strategies.

## Main strategies

A naive strategy would be to always bet on the highest payout, but this doesn't work for three reasons:

- It's impossible to know the real payout until the end of the round, and the bet needs to be made at least a few seconds earlier.
- Others will try to do the same.
- The crowd is usually wise: if most people are betting that the price will go up, the price will probably go up.

Anyway, there are some inefficiencies that my techniques try to exploit.

There are three main classes of strategies: those based on technical indicators, those based on machine learning, and those based on maximizing expected value.

### Strategies based on technical indicators

Don't be fooled by the good results: it's very likely just overfitting. Well, everything about technical analysis is just overfitting. Also, these strategies don't take payouts into account.

Also, not only do these strategies overfit, but they don't take payouts into account. Assuming that many players make predictions based on technical analysis, the payout-weighted accuracy would be low even if the normal accuracy is higher than 50%.

Before the end of a round, the bot loads technical indicators from the TradingView API. If all the indicators indicated in the strategy have the same prediction (bear or bull), the bot places that bet.

The simulator also allows you to compare results with a "control" experiment to estimate the chances of overfitting. How does it work? The control mode will have profitable solutions just by chance. If the number of profitable solutions (and the profit variance) are the same as the results in the search, it is a strong sign of overfitting. That said, keep in mind that overfitting can happen in very subtle ways, so this comparison alone cannot rule it out. Similarly, the p-value is calculated, but a low p-value doesn't mean that there is no overfitting. These tools only show when overfitting is present, not when it's absent.

**Here is my view of technical analysis: it does not work, period. I made this just for fun and to show how the use of technical analysis leads to overfitting. The searcher will produce very profitable solutions, DO NOT use them.**

The searcher allows you to filter profitable solutions with a "training" set and a "validation" set. Notice that the "validation" set doesn't actually validate anything, because many solutions are compared, so profitable solutions are still likely to overfit. **The validation set is only used to show how overfitting happens, not to select profitable solutions!**

### Strategies based on machine learning

I haven't had enough time to test these strategies but my prediction is that they don't work. There is not enough data and the players' behavior drastically changes over time, models are very likely to underfit or overfit.

There are two kind of predictors:

- Price predictors: regressors that predict the closing price in the next round.
- Bet predictors: classifiers that predict the next bet.

Standard predictors don't take payouts into account, except the DQN.

The code for prediction is very simple but it needs some fixing/refactoring, I will do it as soon as I find some time.

### Strategies based on expected value

These strategies aim to maximize either the accuracy (following the wisdom of the crowd), or the payout, or both. They exploit the occasional mismatch between the payout and the wisdom of the crowd (e.g. when a whale bets against the crowd). These are the only strategies that do not overfit and they used to work in the past, but they no longer do, probably because other players had the same ideas and now they are not effective anymore.

Also, most of these strategies tend to bet against whales, and I noticed a high activity from insider traders, here called "assholes". They are usually whales with 100% accuracy and they are hard to detect (they usually play for just a few rounds), invalidating the whole strategy. Some techniques have been developed for asshole detection, but they produce either too many false negatives or too many false positives (in this case, some techniques include a "forgiveness" component so that whales can potentially be removed from the blacklist if their accuracy decreases).

If you are considering copying assholes, I strongly recommend against doing it. First, you would be purposefully practicing a form of insider trading, at least indirectly. This is probably illegal or at least unethical! Second, this strategy wouldn't be profitable anyway. There are many false positives in asshole detection, meaning that you would be mostly copying random players and still lose money in expected value. You have been warned :)