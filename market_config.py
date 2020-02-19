
params = {
    # Sorted list of participants. 
    'PARTICIPANTS' : sorted(['GEN_1', 'GEN_2']),
    
    # This needs to be more than or equal to no_participants * no_bands. 
    'MAX_DEMAND' : 10,
    # Include the last set of bids in the observation space.
    'REVEAL_PREVIOUS_BIDS':True,
    # Give the agent an example of how bidders behaved last time next demand was seen. 
    'PROVIDE_HISTORICAL_CONTEXT':False,
    # In observation, give the agent an accurate forecast of the next demand
    'SHOW_NEXT_DEMAND':True,

    # Demand type - can be one of random, fixed, evolving etc. Defaults to random.
    # 'DEMAND_TYPE':'random', #Random number generator within given range.
    # 'DEMAND_TYPE':'fixed', #Permanently set at half of max.
    'DEMAND_TYPE':'evolving', #Stays put, with low probability (1 in ten) change of moving up or down.

    'NUM_BANDS' : 5,
    'MIN_PRICE' : 0,
    'MAX_PRICE' : 5,
    
    # 'MARKET_SERVER':'tcp://localhost:5570', #local
    'MARKET_SERVER':'tcp://138.68.254.184:5570', #digitalocean market-server - updated with new demand config options.
    # 'MARKET_SERVER':'tcp://178.128.15.200:5570', #digitalocean market-server-test
    # 'MARKET_SERVER':'tcp://206.189.213.129:5570', #digitalocean market-server-test-2 - updated with new demand config options.

}