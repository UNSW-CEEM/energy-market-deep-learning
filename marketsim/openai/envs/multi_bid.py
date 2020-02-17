"""
Classic cart-pole system implemented by Rich Sutton et al.
Copied from http://incompleteideas.net/sutton/book/code/pole.c
permalink: https://perma.cc/C9ZM-652R
"""

import math
import gym
from gym import spaces, logger
from gym.utils import seeding
import numpy as np
from marketsim.logbook.logbook import logbook

from marketsim.io.clients.asyncclient import AsyncClient
from market_config import params as market_config






TOTAL_CAPACITY = float(market_config['MAX_DEMAND']) / float(len(market_config['PARTICIPANTS']))


REDUCE_ACTION_SPACE_SIZE = True

class MultiBidMarket(gym.Env):
    """
    
    """
    
    metadata = {
        'render.modes': ['human'],
        
    }

    def __init__(self):
        obs_high = [
            market_config['MAX_DEMAND'], #demand
            TOTAL_CAPACITY, #Amount Dispatched
            market_config['MAX_PRICE'], #Last Price
        ]

        obs_low = [
            0, #demand
            0, #Amount Dispatched
            0, #Last Price
        ]

        # Create a spot in the observation space for each participant other than this one. 
        if market_config['REVEAL_PREVIOUS_BIDS']:
            for i in range(len(market_config['PARTICIPANTS']) - 1):
                for band in range(market_config['NUM_BANDS']):
                    obs_high.append(market_config['MAX_PRICE'])
                    obs_low.append(market_config['MIN_PRICE'])
        
        # Create a spot in the observation space for each participant other than this one
        # These spots are used to deliver the way the other participants last bid in this context. 
        if market_config['PROVIDE_HISTORICAL_CONTEXT']:
            for i in range(len(market_config['PARTICIPANTS']) - 1):
                self._saved_history = {}
                for band in range(market_config['NUM_BANDS']):
                    obs_high.append(market_config['MAX_PRICE'])
                    obs_low.append(market_config['MIN_PRICE'])

        # Define
        obs_high = np.array(obs_high)
        obs_low = np.array(obs_low)
        print('Obs High:', obs_high)
        print('Obs Low:', obs_low)

        # self.observation_space = spaces.Box(obs_low, obs_high, dtype=np.float32)
        self.observation_space = spaces.Box(obs_low, obs_high )

        
        
        # self.action_space = spaces.Discrete(10)
        try:
            self.action_space = spaces.MultiDiscrete([market_config['MAX_PRICE'] for b in range(market_config['NUM_BANDS'])]) #5 bands of $0 - $9 bids. 
        except: # It seems that in some versions of openai gym, the MultiDiscrete constructor needs an array of high/lows.
            self.action_space = spaces.MultiDiscrete([ [0,market_config['MAX_PRICE']] for b in range(market_config['NUM_BANDS'])]) #5 bands of $0 - $9 bids. 

        self.seed()
        self.viewer = None
        self.state = np.array(obs_low)
        self._state_dict = None

        self.steps_beyond_done = None

        # Need a way to assign or find id.
        self.total_steps = 0
        self.epoch_reward = 0
        self.last_action = 0

    def connect(self, participant_name, id_no):
        print("Connecting as ", participant_name, id_no)
        self.id = id_no
        self.label = participant_name
        self.io = AsyncClient(self.id)
        

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        # print("ACTION: ", action)
        # print(self.action_space)
        # assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
        self.total_steps += 1
        # self.state = (x,x_dot,theta,theta_dot)
        # print("Action:", action)
        self.last_action = action
        
        
        data = {
                'id': self.id,
                'label':self.label,
                'bids' : [ [int(a), TOTAL_CAPACITY / market_config['NUM_BANDS']] for a in action ],
            }
        
        reply = self.io.send(data)
        
        self._state_dict = reply
        
        amount_dispatched = 0 if self.label not in reply['dispatch'] else float(reply['dispatch'][self.label])

        next_state = [
            int(reply['next_demand']) if market_config['SHOW_NEXT_DEMAND'] else 0, #Next Demand
            int(amount_dispatched), #Amount Dispatched
            int(reply['price']), # Last Price,
        ]

        # Add each participant's previous bids to the observation space. 
        # Loop through each participant in the sorted participant list
        if market_config['REVEAL_PREVIOUS_BIDS']:
            for p in market_config['PARTICIPANTS']:
                if p != self.label:
                    prices = [0] * market_config['NUM_BANDS']
                    for bid in reply['all_bids'][p]:
                        prices[bid['band']] = int(bid['price'])
                    # Add the bid info to the observation
                    next_state += prices
        
        # Add each participant's previous bids in a similar demand situation.
        if market_config['PROVIDE_HISTORICAL_CONTEXT']:
            for p in market_config['PARTICIPANTS']:
                if p != self.label:
                    prices = [0] * market_config['NUM_BANDS']
                    if reply['next_demand'] in self._saved_history:
                        for bid in reply['all_bids'][p]:
                            prices[bid['band']] = int(bid['price'])
                    # Add the bid info to the observation
                    next_state += prices
        
            self._saved_history[reply['next_demand']] = reply['all_bids']
        
        # Reward is product of dispatched and 
        reward = amount_dispatched * float(reply['price'])
        
        self.epoch_reward += reward
        # Every day, start a new epoch.
        done = False
        if self.total_steps % 48 == 0:
            done = True
        
        # the next next_state, the reward for the last action, the current next_state, a boolean representing whether the current episode of our model is done and some additional info on our problem
        return np.array(next_state), reward, done, {}

    def reset(self):
        # We used to reset the state each time - dont see how this is sensible as its a continuation in simulation backend. 
        # Still worthwhile having regular epochs as we want it to think about maximising daily bidding (or some other period)
        # But resetting state is a little incompehensible.
        # Edge case here is first instance, whereby state is set to obs_low.
        # self.state = self.np_random.uniform(low=0, high=0.05, size=(8,))
        
        # print(str({"metric": "epoch_reward", "value": self.epoch_reward, "step": self.total_steps}))
        print('{"metric": "epoch_reward", "value": '+str(self.epoch_reward)+', "step":'+str(self.total_steps)+'}')
        
        print('{"metric": "unique_bids", "value": '+str(logbook().get_num_unique_bids(previous_steps=50))+', "step":'+str(self.total_steps)+'}')
        
        logbook().record_epoch_reward(self.epoch_reward)
        self.epoch_reward = 0


        
        # Every X steps, write results to file in case of dramatic failure. 
        if self.total_steps % 200000 == 0:
        # if self.total_steps % 100 == 0:
            logbook().save_json(label=str(self.label))
        
        return np.array(self.state)

    def render(self, mode='human'):
        # Log bid/value in Floydhub
        # print('{"metric": "bid", "value": '+str(self.last_action)+', "step":'+str(self.total_steps)+'}')
        # print("Rendering")
        # Log in logbook suite
        logbook().record_price(self._state_dict['price'], self.total_steps)
        logbook().record_demand(self._state_dict['demand'], self.total_steps)

        
        # Log bidstack in logbook suite.
        for label in self._state_dict['all_bids']:
            for bid in self._state_dict['all_bids'][label]:
                logbook().record_bid(bid['label'], bid['price'], bid['quantity'], self.total_steps)
        return None

    def close(self):
        pass