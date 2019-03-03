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

from marketsim.io.clients.asyncclient import AsyncClient

class SimpleMarket(gym.Env):
    """
    
    """
    
    metadata = {
        'render.modes': ['human'],
        
    }

    def __init__(self):

        # Define
        obs_high = np.array([
                            10000, #demand
                            10, #available MW
                        ])
        obs_low = np.array([
                            0, #demand
                            0, #available MW
                        ])
        # self.observation_space = spaces.Box(obs_low, obs_high, dtype=np.float32)
        self.observation_space = spaces.Box(obs_low, obs_high )

        
        self.action_space = spaces.Discrete(10000)
        self.seed()
        self.viewer = None
        self.state = None

        self.steps_beyond_done = None

        # Need a way to assign or find id.
        self.id = 3
        self.io = AsyncClient(self.id)
        self.label = 'Bayswater'
        self.total_steps = 0

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
        self.total_steps += 1
        # self.state = (x,x_dot,theta,theta_dot)
        # print("Action:", action)
        data = {
                'id': self.id,
                'label':self.label,
                'bids' : [
                    [int(action),10],
                ],
            }
        reply = self.io.send(data)
        
        # state should be a tuple of vals. 
        next_state = (reply['next_demand'],10)
        # Reward is product of dispatched and 
        reward = 0 if self.label not in reply['dispatch'] else float(reply['dispatch'][self.label]) * float(reply['price'])
        
        
        # Every day, start a new epoch.
        done = False
        if self.total_steps % 48 == 0:
            done = True

        # the next next_state, the reward for the last action, the current next_state, a boolean representing whether the current episode of our model is done and some additional info on our problem
        return np.array(next_state), reward, done, {}

    def reset(self):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(2,))
        return np.array(self.state)

    def render(self, mode='human'):
        return None

    def close(self):
        pass