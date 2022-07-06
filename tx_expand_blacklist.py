'''
Expands the blacklist graph by one level, adding all the addresses linked to blacklisted addresses by transactions (except smart contracts).
'''
from modules.blockchain.crawler import Crawler

# the blacklist is a set of addresses (to avoid duplicates when expanding the graph)
CURR_BLACKLIST = {'0x2c2bc495e6ef06cae07a2603ed977fa23e8c23eb'}					# insert initial blacklist here

crawler = Crawler()
new_blacklist = crawler.expand_blacklist_graph(CURR_BLACKLIST, verbose=True)
print(new_blacklist)
