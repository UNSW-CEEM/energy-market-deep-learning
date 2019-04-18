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

class MultiBidMarket(gym.Env):
    """
    
    """
    
    metadata = {
        'render.modes': ['human'],
        
    }

    def __init__(self):

        # Define
        obs_high = np.array([
                            # 10000, #demand
                            1000, #available MW
                        ])
        obs_low = np.array([
                            # 0, #demand
                            0, #available MW
                        ])
        # self.observation_space = spaces.Box(obs_low, obs_high, dtype=np.float32)
        self.observation_space = spaces.Box(obs_low, obs_high )

        
        
        # self.action_space = spaces.Discrete(10)
        try:
            self.action_space = spaces.MultiDiscrete([10,10,10,10,10]) #5 bands of $0 - $9 bids. 
        except: # It seems that in some versions of openai gym, the MultiDiscrete constructor needs an array of high/lows.
            self.action_space = spaces.MultiDiscrete([[0,10],[0,10],[0,10],[0,10],[0,10]]) #5 bands of $0 - $9 bids. 

        self.seed()
        self.viewer = None
        self.state = None
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
                'bids' : [
                    [int(action[0]),200],
                    [int(action[1]),200],
                    [int(action[2]),200],
                    [int(action[3]),200],
                    [int(action[4]),200],
                ],
            }
        reply = self.io.send(data)
        
        self._state_dict = reply
        
        # state should be a tuple of vals. 
        # next_state = (reply['next_demand'],10) 
        next_state = (1000) #taking out next demand
        

        
        
        # Reward is product of dispatched and 
        reward = 0 if self.label not in reply['dispatch'] else float(reply['dispatch'][self.label]) * float(reply['price'])
        
        self.epoch_reward += reward
        # Every day, start a new epoch.
        done = False
        if self.total_steps % 48 == 0:
            done = True

        # the next next_state, the reward for the last action, the current next_state, a boolean representing whether the current episode of our model is done and some additional info on our problem
        return np.array(next_state), reward, done, {}

    def reset(self):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(2,))
        # print(str({"metric": "epoch_reward", "value": self.epoch_reward, "step": self.total_steps}))
        print('{"metric": "epoch_reward", "value": '+str(self.epoch_reward)+', "step":'+str(self.total_steps)+'}')
        logbook().record_epoch_reward(self.epoch_reward)
        self.epoch_reward = 0
        return np.array(self.state)

    def render(self, mode='human'):
        # Log bid/value in Floydhub
        # print('{"metric": "bid", "value": '+str(self.last_action)+', "step":'+str(self.total_steps)+'}')
        
        # Log in logbook suite
        logbook().record_price(self._state_dict['price'], self.total_steps)
        logbook().record_demand(self._state_dict['demand'], self.total_steps)
        # Log bidstack in logbook suite.
        for bid in self._state_dict['all_bids']:
            logbook().record_bid(bid['label'], bid['price'], bid['quantity'], self.total_steps)
        return None

    def close(self):
        pass