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
from threading import Lock
import time
logger = logging.getLogger(__name__)


class Generator():
	def __init__(self, label, capacity_MW):
		self.capacity_MW = capacity_MW
		self.current_output_MW = 0
		self.label = label
		self.type_idx = 0
	
	def get_minimum_next_output_MWh(self, time_step_mins):
		return 0

	def get_maximum_next_output_MWh(self, time_step_mins):
		return self.current_output + 1

	def get_srmc(self):
		return np.float32(0)
	
	def get_lrmc(self):
		return np.float32(0)

	

class Coal_Generator(Generator):
	def __init__(self, label, capacity_MW, ramp_rate_MW_per_min, srmc, lrmc):
		Generator.__init__(self, label, capacity_MW)
		self.ramp_rate_MW_per_min = ramp_rate_MW_per_min
		self.srmc = srmc
		self.lrmc = lrmc
		self.current_output_MW = capacity_MW
		self.type_idx = 1

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
		return np.float32(self.srmc)

	def get_lrmc(self):
		return np.float32(self.lrmc)

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
		self.type_idx = 2

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
		return np.float32(self.srmc)

	def get_lrmc(self):
		return np.float32(self.lrmc)

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
		self.max_time_index = len(self.demand_data)
		
		self.bid_stack_lock = threading.RLock()
		self.reset_lock = threading.RLock()
		

		# Event used to tell if all bids have come in. Makes individual bidders wait for the last bid so we can calculate result of auction.
		self.bid_stack_finalised = threading.Event()
		self.all_finished = threading.Event()

		# Set the minimum and maximum market prices.
		self.min_price = -1000
		self.max_price = 13100
		# Define the participants as a list of generator objects.
		self.generators = {
			'Bayswater': Coal_Generator('Bayswater',12640, 1, 40, 40),
			'Eraring': Coal_Generator('Eraring',2880, 1, 35, 35),
			# 'Liddell': Coal_Generator('Liddell',2000, 7, 35, 35),
			# 'Mt Piper': Coal_Generator('Mt Piper',1400, 1, 30, 30),
			# 'Vales Point B' : Coal_Generator('Vales Point B',1320, 1, 30, 30),
			# 'Colongra': Gas_Turbine_Generator('Colongra',667, 50, 80, 80),
			# 'Liddell': Gas_Turbine_Generator('Liddell',50, 70, 90, 90),
			# 'Tallawarra': Gas_Turbine_Generator('Tallawarra',435, 70, 85, 85),
			# 'Smithfield': Gas_Turbine_Generator('Smithfield',176, 70, 85, 85),
			# 'Uraniquity': Gas_Turbine_Generator('Uraniquity',641, 70, 85, 85),
		}
		
		# Get the maximum generator type available. 
		self.num_generator_types = 0
		for g in self.generators:
			self.num_generator_types = max(self.num_generator_types, self.generators[g].type_idx)

		# Initialise a bid stack.
		self._reset_bid_stack()

		# Keep a register of which participants are finished with their calculations in a given time period. 
		self._reset_finished_register()

		# =========================
		# DEFINING THE OBSERVATION SPACE
		# =========================
		observation_minimums = [
			0, #generator type
			0, # Demand next time period
			0, # Max dispatch this time period
			0, # Min dispatch this time period
			0, # dispatch level last time period
			0, # Marginal price per MWh
			-500, # previous market price per MWh 	
		]
		
		observation_maximums = [
			self.num_generator_types, #generator type. arbitrary limit here on 
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
		print ">>>>>>>>>>> Step Called", generator_label, self.time_index
		
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
			print generator_label, self.time_index, "All Bids Submitted!!"
			# Perform the bid stack calculations - who gets dispatched etc. 
			self._settle_auction()
			# Print the result of the auction
			with self.bid_stack_lock:
				print generator_label, self.time_index, "Auction Settled, bidstack:", self.bid_stacks[self.time_index]
			# Tell the other threads the bid stack is ready.
			self.bid_stack_finalised.set()

		
		else: # Otherwise wait for the others to place bids
			print generator_label, "Waiting"
			# Wait for the others to place bids.
			self.bid_stack_finalised.wait()
			with self.bid_stack_lock:
				print generator_label, self.time_index, "Finished waiting, bid stack has been finalised. ", self.bid_stacks[self.time_index]

		with self.bid_stack_lock:
			# Calculate reward as difference between revenue and cost of generation.
			this_bid = self.bid_stacks[self.time_index][generator_label]
			# print type(this_bid)
			print generator_label, this_bid
			# print this_bid['MWh']
			# print this_bid['price']
			# print this_bid['dispatched']
			dispatched = this_bid['dispatched']
			srmc = generator.get_srmc()
			print generator_label,self.time_index, "Dispatched", dispatched, type(dispatched)
			print generator_label,self.time_index, "SRMC", srmc, type(srmc)
			print generator_label,self.time_index, "Price", self.price, type(self.price)
			# print generator_label, "About to generate error:", self.bid_stacks[self.time_index][generator_label]
			# for thing in self.bid_stacks[self.time_index][generator_label]:
			# 	print thing, self.bid_stacks[self.time_index][generator_label][thing]
			# 	if thing == "dispatched":
			# 		print "FOUND IT!"
			# 		dispatched = self.bid_stacks[self.time_index][generator_label][thing]
			reward = (self.price - srmc) * dispatched
		

		# Get the state as a numpy array
		observations = self._get_observations(generator_label)

		self._record_finished(generator_label)

		self.all_finished.wait()
		# Step time forward by 1 period. 
		# self.time_index += 1
		
		# Check if we are done
		done = True if self.time_index >= len(self.demand_data)-1 else False
		
		

		return observations, reward, done, {}


	def _reset(self):
		print "RESETTING MARKET"
		
		print "Finished Reset Sleep"
		if self.time_index != 0:
			print "Time index has been stepped forward to we will reset all params."
			self.demand_data = getDemandData('PRICE_AND_DEMAND_201701_QLD1.csv')
			self.time_index = 0

			# Event used to tell if all bids have come in. Makes individual bidders wait for the last bid so we can calculate result of auction.
			self.bid_stack_finalised = threading.Event()
			self.all_finished = threading.Event()
			
			# Define the participants as a list of generator objects.
			self.generators = {
				'Bayswater': Coal_Generator('Bayswater',12640, 1, 40, 40),
				'Eraring': Coal_Generator('Eraring',2880, 1, 35, 35),
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

			# Keep a register of who has finished in a given time step.
			self._reset_finished_register()

			# =========================
			# FINISHING SETUP
			# =========================
			self._seed()

		# Create initial set of observations.
		observations = [
			0, # Generator type
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
		print "Resetting Bid Stack"
		with self.bid_stack_lock:
			self.bid_stack_finalised.clear()
			self.bid_stacks = []
			for i in range(self.max_time_index):
				for g in self.generators:
					self.bid_stacks.append({})
					for g in self.generators:
						self.bid_stacks[i][g] = None
	
	def _add_bid(self, generator, MWh, price):
		with self.bid_stack_lock:
			print generator.label, "Adding Bid"
			self.bid_stacks[self.time_index][generator.label] = {'price':price, 'MWh':MWh, 'dispatched':None}
			print generator.label, self.time_index, "Bid stack after add:", self.bid_stacks[self.time_index]
	
	def _all_bids_submitted(self):
		with self.bid_stack_lock:
			# print "Checking submitted, Bid Stack: ", self.bid_stacks[self.time_index]
			for label in self.bid_stacks[self.time_index]:
				if self.bid_stacks[self.time_index][label] == None:
					print "Still waiting on ",label, "to submit a bid."
					return False
		return True


	# Settles the auction based on the assumption that all bids were achievable.
	def _settle_auction(self):
		with self.bid_stack_lock:
			# Get demand in MWh
			demand = float(self.demand_data[self.time_index]) * float(self.time_step_hrs)

			# Get a list of bids from the bid stack
			bids = []
			for gen_label in self.bid_stacks[self.time_index]:
				bid = self.bid_stacks[self.time_index][gen_label]
				bid['label'] = gen_label
				bids.append(bid)
			# Reset price
			self.price = 0
			# Sort the bids by price
			sorted_bids = sorted(bids, key=lambda k: k['price'])
			# dispatch until requirement satisfied.
			
			for bid in sorted_bids:
				
				gen_label = bid['label']
				# Step the price up to match the bid, if there is still dispatch to do.
				if demand > 0:
					print "PRICE", bid['price']
					self.price = bid['price']
				# Find the amount dispatched. Either the demand or what's available. 
				dispatched = min(bid['MWh'], demand)
				# Record the amount dispatched.

				self.bid_stacks[self.time_index][gen_label]['dispatched'] = dispatched
				# Advise the generator to go to requested level

				# Decrement demand, stopping at 0.
				demand = max(demand - dispatched, 0)
	
	def _get_observations(self, generator_label):
		with self.bid_stack_lock:
			generator = self.generators[generator_label]
			observations = [
				generator.type_idx,
				self.demand_data[self.time_index+1], # Demand next time period
				generator.get_maximum_next_output_MWh(self.time_step_mins), # Max dispatch this coming time period for the subject generator
				generator.get_minimum_next_output_MWh(self.time_step_mins), # Min dispatch this coming time period for the subject generator
				self.bid_stacks[self.time_index][generator.label]['dispatched'], # dispatch level last time period for the subject generator
				generator.get_srmc(),  # short-run marginal cost per MWh for the subject generator
				generator.get_lrmc(),  # previous market price per MWh
			]
			# Record each generator's output.
			for g in sorted(self.generators, key=lambda k: k):
				observations.append(self.bid_stacks[self.time_index][g]['dispatched'])
		return np.array(observations)

	def _reset_finished_register(self):
		self.finished_register = []
		for i in range(self.max_time_index):
			dp = {}
			for g in self.generators:
				dp[g] = False
			self.finished_register.append(dp)
	

	def _record_finished(self, generator_label):
		self.finished_register[self.time_index][generator_label] = True
		allFinished = True
		for g in self.finished_register[self.time_index]:
			if self.finished_register[self.time_index][g] == False:
				allFinished = False
				# Make other threads wait until all are done.
				self.all_finished.clear()
				
		if allFinished:
			self.time_index += 1
			# Send out the notification that all can return their values. 
			self.all_finished.set()
			# Reset the bid stack finalisation variable, so all wait at the next step call.
			self.bid_stack_finalised.clear()
		


def getDemandData(path):
	import pandas
	colnames = ['REGION','SETTLEMENTDATE','TOTALDEMAND','RRP','PERIODTYPE']
	data = pandas.read_csv(path, names=colnames, skiprows=[0])
	return np.array(data.TOTALDEMAND.tolist())