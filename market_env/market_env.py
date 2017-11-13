"""
Classic cart-pole system implemented by Rich Sutton et al.
Copied from http://incompleteideas.net/sutton/book/code/pole.c
permalink: https://perma.cc/C9ZM-652R
"""

import logging
import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import pandas
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)


class Generator():
	def __init__(self, label, capacity_MW):
		self.capacity_MW = capacity_MW
		self.current_output_MW = 0
		self.label = label
	
	def get_minimum_next_output_MWh(self, time_step_mins):
		return 0

	def get_maximum_next_output_MWh(self, time_step_mins):
		return self.current_output + 1

	def get_srmc(self):
		return 0
	
	def get_lrmc(self):
		return 0

class Coal_Generator(Generator):
	def __init__(self, label, capacity_MW, ramp_rate_MW_per_min, srmc, lrmc):
		Generator.__init__(self, label, capacity_MW)
		self.ramp_rate_MW_per_min = ramp_rate_MW_per_min
		self.srmc = srmc
		self.lrmc = lrmc
		self.current_output_MW = capacity_MW

	def get_minimum_next_output_MWh(self, time_step_mins):
		# Calculate the maximum output power change.
		maximum_change_MW = float(time_step_mins) * float(self.ramp_rate_MW_per_min)
		# Calculate output if kept steady.
		next_output = float(self.current_output_MW) *  float(time_step_mins) / 60.0
		# Triangle calc to take into account ramping down.
		next_output = next_output - 0.5 * float(maximum_change_MW) * float(time_step_mins) / 60.0
		# Make sure if next min output is below zero, we just return 0
		return max(next_output, 0)

	def get_maximum_next_output_MWh(self, time_step_mins):
		# Calculate the maximum output power change.
		maximum_change_MW = float(time_step_mins) * float(self.ramp_rate_MW_per_min)
		# Calculate output if kept steady.
		next_output = float(self.current_output_MW) *  float(time_step_mins) / 60.0
		# Triangle calc to take into account ramping up.
		next_output = next_output + 0.5 * float(maximum_change_MW) * float(time_step_mins) / 60.0
		# Make sure if next min output above the capacity, we just return the energy generated at capacity
		return min(next_output, float(self.capacity_MW) * float(time_step_mins) / 60.0)

	def get_srmc(self):
		return self.srmc

	def get_lrmc(self):
		return self.lrmc	

	def set_output_MW(self, MW, time_step_mins):
		maximum = self.get_maximum_next_output_MWh(time_step_mins)
		minimum = self.get_minimum_next_output_MWh(time_step_mins)
		if MW > maximum:
			self.current_output_MW = maximum * 60.0 / time_step_mins
		elif MW < minimum:
			self.current_output_MW = minimum * 60.0 / time_step_mins
		else:
			self.current_output_MW = MW

class Gas_Turbine_Generator(Generator):
	def __init__(self, label, capacity_MW, ramp_rate_MW_per_min, srmc, lrmc):
		Generator.__init__(self, label, capacity_MW)
		self.ramp_rate_MW_per_min = ramp_rate_MW_per_min
		self.srmc = srmc
		self.lrmc = lrmc

	def get_minimum_next_output_MWh(self, time_step_mins):
		# Calculate the maximum output power change.
		maximum_change_MW = float(time_step_mins) * float(self.ramp_rate_MW_per_min)
		# Calculate output if kept steady.
		next_output = float(self.current_output_MW) *  float(time_step_mins) / 60.0
		# Triangle calc to take into account ramping down.
		next_output = next_output - 0.5 * float(maximum_change_MW) * float(time_step_mins) / 60.0
		# Make sure if next min output is below zero, we just return 0
		return max(next_output, 0)

	def get_maximum_next_output_MWh(self, time_step_mins):
		# Calculate the maximum output power change.
		maximum_change_MW = float(time_step_mins) * float(self.ramp_rate_MW_per_min)
		# Calculate output if kept steady.
		next_output = float(self.current_output_MW) *  float(time_step_mins) / 60.0
		# Triangle calc to take into account ramping up.
		next_output = next_output + 0.5 * float(maximum_change_MW) * float(time_step_mins) / 60.0
		# Make sure if next min output above the capacity, we just return the energy generated at capacity
		return min(next_output, float(self.capacity_MW) * float(time_step_mins) / 60.0)

	def get_srmc(self):
		return self.srmc

	def get_lrmc(self):
		return self.lrmc	

class Single_Ownership_Market_Interface(object):
	def __init__(self, market, label):
		self.market = market 
		self.label = label
	def seed(self, seed=None):
		return self.market._seed(seed)
	def step(self, action):
		return self.market.step(action, self.label)
	def reset(self):
		return self.market._reset()
	def render(self, mode='human', close=False):
		return self.market._render(mode=mode, close=close)

class ElectricityMarket(gym.Env):
	metadata = {
		'render.modes': ['human', 'rgb_array'],
		'video.frames_per_second' : 50
	}

	def __init__(self):
		print "Initialising Market Environment."
		self.demand_data = getDemandData('PRICE_AND_DEMAND_201701_QLD1.csv')
		self.time_index = 0
		self.time_step_mins = 30
		self.time_step_hrs = self.time_step_mins / 60.0

		# Event used to tell if all bids have come in. Makes individual bidders wait for the last bid so we can calculate result of auction.
		self.bid_stack_ready = threading.Event()
		# Set the minimum and maximum market prices.
		self.min_price = -1000
		self.max_price = 13100
		# Define the participants as a list of generator objects.
		self.generators = {
			'Bayswater': Coal_Generator('Bayswater',12640, 1, 40, 40),
			# 'Eraring': Coal_Generator('Eraring',2880, 1, 35, 35),
			# 'Liddell': Coal_Generator('Liddell',2000, 7, 35, 35),
			# 'Mt Piper': Coal_Generator('Mt Piper',1400, 1, 30, 30),
			# 'Vales Point B' : Coal_Generator('Vales Point B',1320, 1, 30, 30),
			# 'Colongra': Gas_Turbine_Generator('Colongra',667, 50, 80, 80),
			# 'Liddell': Gas_Turbine_Generator('Liddell',50, 70, 90, 90),
			# 'Tallawarra': Gas_Turbine_Generator('Tallawarra',435, 70, 85, 85),
			# 'Smithfield': Gas_Turbine_Generator('Smithfield',176, 70, 85, 85),
			# 'Uraniquity': Gas_Turbine_Generator('Uraniquity',641, 70, 85, 85),
		}

		# Initialise a bid stack.
		self._reset_bid_stack()

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
			100000, # Demand
			100000, # Max dispatch this time period for the subject generator
			100000, # Min dispatch this time period for the subject generator
			100000, # dispatch level last time period for the subject generator
			13100,  # short-run marginal cost per MWh for the subject generator
			13100,  # previous market price per MWh
		]

		# For each generator, add a spot in the observation space for current output. 
		# Minimum 0 maximum 10000 (arbitrary)
		# Later, we will make this more relevant to each generator
		for label in self.generators:
			g = self.generators[label]
			observation_minimums.append(0)
			observation_maximums.append(float(g.capacity_MW) * self.time_step_hrs)
		# Define the observation space, based on the minimums and maximums set. 
		self.observation_space = spaces.Box(np.array(observation_minimums), np.array(observation_maximums))

		# =========================
		# DEFINING THE ACTION SPACE
		# =========================
		# These are representations of the min and max values for an action
		# First col is  MWh, second is price. 
		low_bid = np.array([ 0,self.min_price])
		high_bid = np.array([ 15000, self.max_price])

		# Define the action space - can be any number from the mins in low_bid to the axes in high_bid
		self.action_space = spaces.Box(low_bid,high_bid)

		# =========================
		# FINISHING SETUP
		# =========================
		self._seed()
		self.viewer = None
		# self.state = None

		

	def _seed(self, seed=None):
		self.np_random, seed = seeding.np_random(seed)
		return [seed]

	def step(self, action, generator_label):
		return self._step(action, generator_label)

	def _step(self, action, generator_label):
		# A bid has been submitted, make sure all threads are going to wait until ready.
		if self.bid_stack_ready.isSet():
			self.bid_stack_ready.clear()
		
		# Step time forward by 1 period. 
		self.time_index += 1
		
		# Check if we are done
		done = True if self.time_index >= len(self.demand_data)-1 else False
		
		# Make sure the action is valid.
		# assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
		
		# Get the bid from the submitted action.
		bid_MWh = action[0]
		bid_price = action[1]
		generator = self.generators[generator_label]
		
		# If bid acceptable, place bid in bidstack.
		self._add_bid(generator, bid_MWh, bid_price)
		
		#Now that we've submitted our bid, check if it's the last one. 
		if self._all_bids_submitted(): 
			print "All Bids Submitted!!"
			# Perform the bid stack calculations - who gets dispatched etc. 
			self._settle_auction()
			# Tell the other threads the bid stack is ready.
			self.bid_stack_ready.set()
		
		else: # Otherwise wait for the others to place bids
			print "Waiting -> ", generator_label
			# Wait for the others to place bids.
			self.bid_stack_ready.wait()

		# Calculate reward as difference between revenue and cost of generation.
		reward = (self.price - generator.get_srmc()) * self.bid_stack[generator.label]['dispatched']

		# Get the state as a numpy array
		observations = self._get_observations(generator_label)

		return observations, reward, done, {}

	def _reset(self):
		print "RESETTING MARKET"
		self.demand_data = getDemandData('PRICE_AND_DEMAND_201701_QLD1.csv')
		self.time_index = 0

		# Event used to tell if all bids have come in. Makes individual bidders wait for the last bid so we can calculate result of auction.
		self.bid_stack_ready = threading.Event()
		
		# Define the participants as a list of generator objects.
		self.generators = {
			'Bayswater': Coal_Generator('Bayswater',12640, 1, 40, 40),
			# 'Eraring': Coal_Generator('Eraring',2880, 1, 35, 35),
			# 'Liddell': Coal_Generator('Liddell',2000, 7, 35, 35),
			# 'Mt Piper': Coal_Generator('Mt Piper',1400, 1, 30, 30),
			# 'Vales Point B' : Coal_Generator('Vales Point B',1320, 1, 30, 30),
			# 'Colongra': Gas_Turbine_Generator('Colongra',667, 50, 80, 80),
			# 'Liddell': Gas_Turbine_Generator('Liddell',50, 70, 90, 90),
			# 'Tallawarra': Gas_Turbine_Generator('Tallawarra',435, 70, 85, 85),
			# 'Smithfield': Gas_Turbine_Generator('Smithfield',176, 70, 85, 85),
			# 'Uraniquity': Gas_Turbine_Generator('Uraniquity',641, 70, 85, 85),
		}

		# Initialise a bid stack.
		self._reset_bid_stack()

		# =========================
		# FINISHING SETUP
		# =========================
		self._seed()

		# Create initial set of observations.
		observations = [
			self.demand_data[0], # Demand next time period
			1, # Max dispatch this coming time period for the subject generator
			0, # Min dispatch this coming time period for the subject generator
			0, # dispatch level last time period for the subject generator
			0,  # short-run marginal cost per MWh for the subject generator
			0,  # previous market price per MWh
		]
		# Record each generator's output.
		for g in sorted(self.generators, key=lambda k: k):
			observations.append(0)
		return np.array(observations)

	def _render(self, mode='human', close=False):
		return None
		# if close:
		# 	if self.viewer is not None:
		# 		self.viewer.close()
		# 		self.viewer = None
		# 	return

		# screen_width = 600
		# screen_height = 400

		# world_width = self.x_threshold*2
		# scale = screen_width/world_width
		# carty = 100 # TOP OF CART
		# polewidth = 10.0
		# polelen = scale * 1.0
		# cartwidth = 50.0
		# cartheight = 30.0

		# if self.viewer is None:
		# 	 from gym.envs.classic_control import rendering
		# 	 self.viewer = rendering.Viewer(screen_width, screen_height)
			#  l,r,t,b = -cartwidth/2, cartwidth/2, cartheight/2, -cartheight/2
			#  axleoffset =cartheight/4.0
			#  cart = rendering.FilledPolygon([(l,b), (l,t), (r,t), (r,b)])
			#  self.carttrans = rendering.Transform()
			#  cart.add_attr(self.carttrans)
			#  self.viewer.add_geom(cart)
			#  l,r,t,b = -polewidth/2,polewidth/2,polelen-polewidth/2,-polewidth/2
			#  pole = rendering.FilledPolygon([(l,b), (l,t), (r,t), (r,b)])
			#  pole.set_color(.8,.6,.4)
			#  self.poletrans = rendering.Transform(translation=(0, axleoffset))
			#  pole.add_attr(self.poletrans)
			#  pole.add_attr(self.carttrans)
			#  self.viewer.add_geom(pole)
			#  self.axle = rendering.make_circle(polewidth/2)
			#  self.axle.add_attr(self.poletrans)
			#  self.axle.add_attr(self.carttrans)
			#  self.axle.set_color(.5,.5,.8)
			#  self.viewer.add_geom(self.axle)
			#  self.track = rendering.Line((0,carty), (screen_width,carty))
			#  self.track.set_color(0,0,0)
			#  self.viewer.add_geom(self.track)

		# if self.state is None: return None

		# x = self.state
		# cartx = x[0]*scale+screen_width/2.0 # MIDDLE OF CART
		# self.carttrans.set_translation(cartx, carty)
		# self.poletrans.set_rotation(-x[2])

		# return self.viewer.render(return_rgb_array = mode=='rgb_array')

	def _reset_bid_stack(self):
		self.bid_stack = {}
		for g in self.generators:
			self.bid_stack[g] = None
	
	def _add_bid(self, generator, MWh, price):
		self.bid_stack[generator.label] = {'price':price, 'MWh':MWh}
	
	def _all_bids_submitted(self):
		for label in self.bid_stack:
			if self.bid_stack[label] == None:
				return False
		return True

	# Settles the auction based on the assumption that all bids were achievable.
	def _settle_auction(self):
		print "Settling Auction"
		# Get demand in MWh
		demand = float(self.demand_data[self.time_index]) * float(self.time_step_hrs)
		print "Demand:", demand
		# Get a list of bids from the bid stack
		bids = []
		for gen_label in self.bid_stack:
			bid = self.bid_stack[gen_label]
			bid['label'] = gen_label
			bids.append(bid)
		# Sort the bids by price
		sorted_bids = sorted(bids, key=lambda k: k['price'])
		# dispatch until requirement satisfied.
		for bid in sorted_bids:
			print "Demand:", demand
			gen_label = bid['label']
			# Step the price up to match the bid, if there is still dispatch to do.
			if demand > 0:
				print "PRICE", bid['price']
				self.price = bid['price']
			# Find the amount dispatched. Either the demand or what's available. 
			dispatched = min(bid['MWh'], demand)
			# Record the amount dispatched.
			self.bid_stack[gen_label]['dispatched'] = dispatched
			# Advise the generator to go to requested level

			# Decrement demand, stopping at 0.
			demand = max(demand - dispatched, 0)
	
	def _get_observations(self, generator_label):
		generator = self.generators[generator_label]
		observations = [
			self.demand_data[self.time_index+1], # Demand next time period
			generator.get_maximum_next_output_MWh(self.time_step_mins), # Max dispatch this coming time period for the subject generator
			generator.get_minimum_next_output_MWh(self.time_step_mins), # Min dispatch this coming time period for the subject generator
			self.bid_stack[generator.label]['dispatched'], # dispatch level last time period for the subject generator
			generator.get_srmc(),  # short-run marginal cost per MWh for the subject generator
			generator.get_lrmc(),  # previous market price per MWh
		]
		# Record each generator's output.
		for g in sorted(self.generators, key=lambda k: k):
			observations.append(self.bid_stack[g]['dispatched'])
		return np.array(observations)


def getDemandData(path):
	import pandas
	colnames = ['REGION','SETTLEMENTDATE','TOTALDEMAND','RRP','PERIODTYPE']
	data = pandas.read_csv(path, names=colnames, skiprows=[0])
	return np.array(data.TOTALDEMAND.tolist())