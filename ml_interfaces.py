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
		self.dispatch = None
		self.dispatch_event = Event()
		self.dispatch_event.clear()

		self.hours_in_time_period = 0.5
		
		self.participant = Single_Ownership_Participant(generator_label, self.dispatch_callback)
		# =========================
		# DEFINING THE OBSERVATION SPACE
		# =========================
		observation_minimums = [
			
			0, # Demand next time period
			0, # Max dispatch this time period
			0, # Min dispatch this time period
			0, # dispatch level last time period
			0, # Marginal price per MWh
			-500, # previous market price per MWh 	
		]
		
		observation_maximums = [
			
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

		# Hours in each time period. ie. 30 minute intervals assumed here.
		for label in self.generators:
			g = self.generators[label]
			observation_minimums.append(0)
			observation_maximums.append(float(g['capacity_MW']) * self.hours_in_time_period)

		# Define the observation space, based on the minimums and maximums set. 
		self.observation_space = spaces.Box(np.array(observation_minimums), np.array(observation_maximums))

		
		# =========================
		# DEFINING THE ACTION SPACE
		# =========================
		# These are representations of the min and max values for an action
		# First col is  MWh, second is price. 
		low_bid = np.array([ 0,-1000])
		high_bid = np.array([ self.generators[generator_label]['capacity_MW'] * 0.5, 13100])

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
		bid_MWh = action[0]
		bid_price = action[1]

		print self.generator_label, "Adding Bid", bid_price, bid_MWh
		# Send the bid command to the participant
		self.participant.add_bid(bid_price, bid_MWh)

		# Wait for dispatch event.
		self.dispatch_event.wait()
		print "ML", "Step -> Dispatched", self.dispatch
		self.dispatch_event.clear()

		# Create an observations array
		observations = [
				self.dispatch['next_demand'], # Demand next time period
				self.dispatch['minimum_next_output_MWh'][self.generator_label], # Max dispatch this coming time period for the subject generator
				self.dispatch['maximum_next_output_MWh'][self.generator_label], # Min dispatch this coming time period for the subject generator
				self.dispatch['dispatch'][self.generator_label], # dispatch level last time period for the subject generator
				self.dispatch['srmc'][self.generator_label],  # short-run marginal cost per MWh for the subject generator
				self.dispatch['lrmc'][self.generator_label],  # previous market price per MWh
			]
		# Then add the dispatch of each generator.
		observations.extend([self.dispatch['dispatch'][g] for g in self.generators])
		

		# Calculate reward - need to update later with penalties etc.
		reward = self.dispatch['dispatch'][self.generator_label] * self.dispatch['price']
		
		# Check whether done
		done = self.dispatch['done']
		# return the observation
		return observations, reward, done, {}

	def dispatch_callback(self, dispatch):
		# print "ML", "Callback -> Dispatched", dispatch
		self.dispatch = dispatch
		self.dispatch_event.set()

	def reset(self):
		self._seed()
		# Send a reset request to the participant, which sends one to the market.
		# Returns observations from the new (reset) state 
		return None

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
	