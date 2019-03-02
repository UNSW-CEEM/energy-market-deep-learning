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
        high = np.array([
                            3,
                            np.finfo(np.float32).max,
                            3,
                            np.finfo(np.float32).max])
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)

        self.seed()
        self.viewer = None
        self.state = None

        self.steps_beyond_done = None

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
        
        # self.state = (x,x_dot,theta,theta_dot)
        
        # state should be a tuple of vals. 
        next_state = (1,2,3,4)
        reward = 2
        done = True
        # the next next_state, the reward for the current next_state, a boolean representing whether the current episode of our model is done and some additional info on our problem
        return np.array(next_state), reward, done, {}

    def reset(self):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        return np.array(self.state)

    def render(self, mode='human'):
        return None

    def close(self):
        pass