from market_config import params as market_config
import itertools



# First, we generate every possible bid.
# for band in bands:



prices = range(market_config['MAX_PRICE'])
bands = range(market_config['NUM_BANDS'])
# Cartesian product gives you permutations with replacement, as at https://stackoverflow.com/questions/14006867/python-itertools-permutations-how-to-include-repeating-characters
bid_permutations = itertools.product(prices, repeat=len(bands))
bid_permutations = [x for x in bid_permutations]
unique_bids = {}
counter = 0
for perm in bid_permutations:
    perm = tuple(sorted(perm))

    if not perm in unique_bids:
        unique_bids[perm] = counter
        counter += 1
        
print(len(unique_bids))