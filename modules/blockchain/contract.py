import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware
from utils.contract import PREDICTION_ABI
from utils.config import Blockchain, BotStrategy, StrategyParams
from utils.const import Transactions

class Contract:
	'''
	Handles all the operations made on the dApp contract and other blockchain operations.
	'''
	w3 = None
	address = None
	private_key = None
	contract_address = None
	contract = None
	txs_query = None
	reference_block = None
	reference_timestamp = None

	def __init__(self):
		'''
		Initializes the web3 instance for the blockchain-related operations. Also initializes the contract and address info.
		'''
		# bsc node
		self.w3 = Web3(Web3.HTTPProvider(Blockchain.HTTP_NODE))
		self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
		# my address info
		self.address = self.w3.toChecksumAddress(Blockchain.ADDRESS)
		self.private_key = str(Blockchain.WALLET_PRIVATE_KEY).lower()
		# contract and query
		self.contract_address = self.w3.toChecksumAddress(Blockchain.CONTRACT_ADDRESS)
		self.contract = self.w3.eth.contract(address=self.contract_address, abi=PREDICTION_ABI)
		self.refresh()

	def load_epoch(self, epoch):
		'''
		Loads contract data from a specific epoch.
		'''
		return self.contract.functions.rounds(epoch).call()

	def load_current_epoch(self):
		'''
		Loads contract data from the current epoch.
		'''
		return self.contract.functions.currentEpoch().call()

	def is_paused(self):
		'''
		Checks if the market is paused.
		'''
		return self.contract.functions.paused().call()

	def refresh(self):
		'''
		Refreshes the contract query, called when something goes wrong.
		'''
		# get latest block
		latest_block = self.w3.eth.get_block('latest')['number']
		# get all txs from the latest N blocks (N = BotStrategy.BLOCKS_OFFSET)
		self.txs_query = self.w3.eth.filter({'address': self.contract_address, 'fromBlock': latest_block - BotStrategy.BLOCKS_OFFSET, 'toBlock': 'latest'})

	def execute_transaction_bet(self, bet_type, bet_amount, epoch, fee=Blockchain.MIN_GAS_PRICE):
		'''
		Executes a bet transaction on the contract (BetBull or BetBear).
		'''
		bet_value = self.w3.toWei(bet_amount, 'ether')
		bet = None
		fee = int(fee if fee < Blockchain.MAX_GAS_PRICE else Blockchain.MAX_GAS_PRICE)		# let's double check because I'm paranoid
		try:
			tx_data = self.__get_tx_data(bet_value, fee)
			if bet_type == Transactions.BET_BULL:
				bet = self.contract.functions.betBull(epoch).buildTransaction(tx_data)
			elif bet_type == Transactions.BET_BEAR:
				bet = self.contract.functions.betBear(epoch).buildTransaction(tx_data)
		except Exception as e:
			print(f'New round fail - {e}')
		return bet

	def execute_transaction_claim(self, epochs):
		'''
		Executes a claim transaction on the contract, passing a list of epochs to claim as input.
		'''
		try:
			return self.contract.functions.claim(epochs).buildTransaction(self.__get_tx_data(0, int(Blockchain.MIN_GAS_PRICE)))
		except Exception as e:
			print(f'New round fail - {e}')
		return None

	def sign_transaction(self, tx):
		'''
		Signs a transaction with the private key.
		'''
		return self.w3.eth.account.signTransaction(tx, private_key=self.private_key)

	def send_transaction(self, tx):
		'''
		Sends a signed transaction to the blockchain.
		'''
		self.w3.eth.sendRawTransaction(tx.rawTransaction)

	def get_transaction_receipt(self, tx):
		'''
		Retrieves the transaction receipt from the blockchain.
		'''
		return self.w3.eth.waitForTransactionReceipt(tx.hash)

	def __get_tx_data(self, value, gas_price):
		'''
		Returns the transaction data for the contract.
		'''
		return {
			'from': self.address,
			'nonce': self.w3.eth.getTransactionCount(self.address),
			'value': value,
			'gas': Blockchain.GAS,
			'gasPrice': gas_price,
		}

	def retrieve_round_txs(self):
		'''
		Retrieves all the transactions from the current round.
		'''
		self.refresh()
		response = self.txs_query.get_all_entries()
		return self.__process_retrieved_txs(response)

	def retrieve_new_txs(self):
		'''
		Retrieves new transactions from the current round.
		'''
		response = self.txs_query.get_new_entries()
		return self.__process_retrieved_txs(response)

	def __process_retrieved_txs(self, elems):
		'''
		Processes the retrieved transactions by extracting the relevant info. Extracts the timestamp from the block data.
		The timestamp resolution is 3 seconds.
		'''
		# TODO PH remove duplicates
		# get only the first non-None block
		first_block = None
		first_timestamp = None
		txs = []
		# if it doesn't get the timestamp, use the previous one
		for elem in elems:
			tx = self.w3.eth.get_transaction(elem['transactionHash'])
			block = tx['blockNumber']
			# print(block)
			tx = {'from': tx['from'], 'value': tx['value'], 'input': tx['input']}
			# if there is no block, it means that the tx is pending, also the block doesn't refresh until it's completed
			use_reference = True
			if first_block:
				if block:
					block_diff = block - first_block
					time_diff = block_diff * StrategyParams.AVG_BLOCK_DURATION
					timestamp = first_timestamp + time_diff
					use_reference = False
			elif block:
				try:
					timestamp = self.w3.eth.get_block(block)['timestamp']
					first_block = block
					first_timestamp = timestamp
					use_reference = False
				except ValueError as e:
					# this is usually raised when the block is not yet completed,
					# I'll just ignore the best practices here and leave the exception unhandled,
					# otherwise the log will get unnecessarily messy
					pass
			if use_reference:
				block = self.reference_block
				timestamp = self.reference_timestamp
			# TODO it shouldn't get stuck, but if it does, consider detecting it and incrementing reference_block by 1
			self.reference_block = block
			self.reference_timestamp = timestamp
			tx['timeStamp'] = self.reference_timestamp
			txs.append(tx)
		return txs

	def get_txs_from_block(self, block):
		'''
		Retrieves transactions starting from a given block (max 10000).
		'''
		# TODO using bscscan api because I found it easier when I started, convert to w3 (it's already here commmented, I just have to test it)
		# # w3 filter that gets all txs from contract starting from block
		# txs_query = self.w3.eth.filter({'address': self.contract_address, 'fromBlock': block, 'toBlock': 'latest'})
		# # make the query and return the results; print error if there is a timeout instead
		# try:
		# 	response = txs_query.get_all_entries()
		# except TimeoutError as e:
		# 	print(f'Timeout error - {e}')
		# 	return []
		# return response # self.__process_retrieved_txs(response)
		url = 'https://api.bscscan.com/api' + \
				'?module=account' + \
				'&action=txlist' + \
				'&address=' + Blockchain.CONTRACT_ADDRESS + \
				'&startblock=' + str(block) + \
				'&sort=asc' + \
				'&apikey=' + Blockchain.BSCSCAN_KEY
		try:
			return requests.get(url, timeout=Blockchain.TIMEOUT).json()['result']
		except requests.exceptions.Timeout as e:
			print('Timeout')
		return None

	def get_address_txs(self, address):
		'''
		Retrieves the latest transactions from an address.
		'''
		# TODO refactor this to w3. Consider moving to a new class (in blockchain.__init__.py)
		url = 'https://api.bscscan.com/api' + \
				'?module=account' + \
				'&action=txlist' + \
				'&address=' + address + \
				'&page=1' + \
				'&offset=500' + \
				'&sort=desc' + \
				'&apikey=' + Blockchain.BSCSCAN_KEY
		try:
			return requests.get(url, timeout=Blockchain.TIMEOUT).json()['result']
		except requests.exceptions.Timeout as e:
			print('Timeout')
		return None