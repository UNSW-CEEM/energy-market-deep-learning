import os
params = {
    # Sorted list of participants. 
    'PARTICIPANTS' : sorted(['Luke']),
    

    # This needs to be more than or equal to no_participants * no_bands. 
    'MAX_DEMAND' : 20,
    # Include the last set of bids in the observation space.
    'REVEAL_PREVIOUS_BIDS':True,
    # Give the agent an example of how bidders behaved last time next demand was seen. 
    'PROVIDE_HISTORICAL_CONTEXT':True,
    # In observation, give the agent an accurate forecast of the next demand
    'SHOW_NEXT_DEMAND':True,

    'NUM_BANDS' : 5,
    'MIN_PRICE' : 0,
    'MAX_PRICE' : 10,

    'DB_NAME':os.environ['DB_NAME'],
    'MONGO_USER':os.environ['MONGO_USER'],
    'MONGO_PASSWORD':os.environ['MONGO_PASSWORD'],
    'MONGO_HOST':os.environ['MONGO_HOST'],
    'MONGO_PORT':os.environ['MONGO_PORT'],
    'MONGO_AUTH_SOURCE':os.environ['MONGO_AUTH_SOURCE'],

}