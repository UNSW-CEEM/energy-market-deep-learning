# Implements the interface described here https://gym.openai.com/docs/


import logging
import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import pandas
from collections import OrderedDict
import threading
from threading import Lock, Event
import time
from collections import OrderedDict
from ws_participant_sim import Single_Ownership_Participant
logger = logging.getLogger(__name__)

class Single_Ownership_Participant_Interface(gym.Env):

	# Eventually I want the list of generators to come from the Market model after registration. But for now we pass it from the ML setup.
	def __init__(self, generator_label, generators, lrmc, capacity_MW):
		self.generators = OrderedDict(generators)
		self.capacity_MW = capacity_MW
		self.lrmc = lrmc
		self.generator_label = generator_label
		
		# Holds info about dispatch
		self.market_state = None
		self.dispatch_event = Event()
		self.dispatch_event.clear()

		# Holds info about reset
		self.reset_event = Event()
		self.reset_event.clear()

		self.hours_in_time_period = 0.5
		
		self.participant = Single_Ownership_Participant(generator_label, self.dispatch_callback, self.reset_callback)
		# =========================
		# DEFINING THE OBSERVATION SPACE
		# =========================
		observation_minimums = [
			0, # Fresh Reset Flag
			0, # Demand next time period
			0, # Max dispatch this time period
			0, # Min dispatch this time period
			0, # dispatch level last time period
			0, # Marginal price per MWh
			-500, # previous market price per MWh 	
		]
		
		observation_maximums = [
			1,      # Fresh Reset Flag
			100000, # Demand next time period
			100000, # Max dispatch this time period for the subject generator
			100000, # Min dispatch this time period for the subject generator
			100000, # dispatch level last time period for the subject generator
			13100,  # short-run marginal cost per MWh for the subject generator
			13100,  # previous market price per MWh
		]

		# For each generator, add a spot in the observation space for current output. 
		# Minimum 0 maximum 10000 (arbitrary)
		# Later, we will make this more relevant to each generator
		observation_minimums.extend([0 for g in self.generators])
		observation_maximums.extend( [ float(self.generators[g]['capacity_MW']) * self.hours_in_time_period for g in self.generators ] )
		
		# Define the observation space, based on the minimums and maximums set. 
		self.observation_space = spaces.Box(np.array(observation_minimums), np.array(observation_maximums))

		# =========================
		# DEFINING THE ACTION SPACE
		# =========================
		# These are representations of the min and max values for an action
		# First col is  MWh, second is price. 
		low_bid = np.array([ 0, -1000])
		high_bid = np.array([ self.generators[generator_label]['capacity_MW'] * 0.5, 14900])

		# Define the action space - can be any number from the mins in low_bid to the axes in high_bid
		self.action_space = spaces.Box(low_bid,high_bid)

		# =========================
		# FINISHING SETUP
		# =========================
		self._seed()
		self.viewer = None
		# self.state = None

	def seed(self, seed=None):
		self.np_random, seed = seeding.np_random(seed)
		return [seed]

	def step(self, action):
		print "MLI step called", action 
		bid_MWh = action[0] if not np.isnan(action[0])else 0
		bid_price = action[1] if not np.isnan(action[1]) else 0
		print self.generator_label, "Adding Bid", bid_price, bid_MWh
		# Send the bid command to the participant
		self.participant.add_bid(bid_price, bid_MWh)
		# Wait for dispatch event.
		self.dispatch_event.wait()
		# print "MLI", "Step -> Dispatched", self.market_state
		self.dispatch_event.clear()
		# Create an observations array
		observations = self.generate_observations(self.market_state)
		# Calculate reward - need to update later with penalties etc.
		reward = self.market_state['dispatch'][self.generator_label] * (self.market_state['price'] - self.market_state['srmc'][self.generator_label])
		
		if bid_price < -1000:
			reward = -1490000000 #if we set reward to 0 here, there's actually an improvement going below -1000 as opposed to getting a negative reward
		if bid_MWh < 0:
			reward = -1490000000
		

		print "Reward", reward
		# Check whether done
		done = self.market_state['done']
		# return the observation
		return observations, reward, done, {}

	# Given a response from the model that contains general state information, generate a set of observations
	# In the format requred by OpenAI Gym
	def generate_observations(self, model_state):
		print "Generating Observations. Model:", model_state
		# Create an observations array
		observations = [
			0, # 1 if 'fresh_reset' in model_state else 0,
			model_state['next_demand'], # Demand next time period
			model_state['minimum_next_output_MWh'][self.generator_label], # Max dispatch this coming time period for the subject generator
			model_state['maximum_next_output_MWh'][self.generator_label], # Min dispatch this coming time period for the subject generator
			model_state['dispatch'][self.generator_label], # dispatch level last time period for the subject generator
			model_state['srmc'][self.generator_label],  # short-run marginal cost per MWh for the subject generator
			model_state['lrmc'][self.generator_label],  # previous market price per MWh
		]
		# Then add the dispatch of each generator. Gens are pulled from an ordered list. 
		observations.extend([model_state['dispatch'][g] if g in model_state['dispatch'] else 0 for g in self.generators])
		return observations

	def dispatch_callback(self, state):
		# print "MLI", "Callback -> Dispatched", dispatch
		self.market_state = state
		self.dispatch_event.set()

	# Send a reset request to the participant, which sends one to the market.
	def reset(self):
		print "RESET CALLED"
		# I'm omitting actual reset in implementation
		# - a lot of philosophical questions here, but effectively, there's no point resetting the market. 
		# Any starting point is as good as any other. 
		self._seed()
		self.participant.reset()
		# Wait for the callback to be called that indicates a reset has happened.
		self.reset_event.wait()
		print "MLI","Successfully reset. State: ", self.market_state
		self.reset_event.clear()

		# Returns observations from the new (reset) state 
		return self.generate_observations(self.market_state)

	def reset_callback(self, state):
		self.market_state = state
		self.reset_event.set()

	def render(self, mode='human', close=False):
		return None
		# return self.market._render(mode=mode, close=close)


if __name__ == "__main__":

	gens = {
		'Bayswater':{
			'type':'coal',
			'capacity_MW':3000,
			'lrmc':30,
		},
		# 'Eraring':{
		# 	'type':'coal',
		# 	'capacity_MW':1000,
		# 	'lrmc':70
		# },
	}
	p1 = Single_Ownership_Participant_Interface('Bayswater', gens, 30, 3000 )
	
	for i in range(100):
		print p1.step([3000,i])
	
	print "Resetting"
	print p1.reset()

	result = p1.step([3000,1])
	print "Final result", result
	