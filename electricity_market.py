# An events-based electricity market simulator.
import config
import generators

class Electricity_Market():
	# Called when a new electricity market object is created. 
	def __init__(self, dispatch_callback):
		# Keep track of the current time period. 
		self.time_period = 0
		# Store the number of minutes per time period
		self.period_length_mins = 30
		# generators is a list of generator objects.
		self.generators = {g:generators.Coal_Generator(label=g, capacity_MW = config.generators[g]['capacity_MW'], ramp_rate_MW_per_min = config.generators[g]['ramp_rate_MW_per_min'], srmc = config.generators[g]['srmc'], lrmc = config.generators[g]['lrmc']) for g in config.generators}
		# bids is a dictthat stores a bid value for each generator
		self.bidstack = {g : None for g in config.generators}
		# Function that is called when dispatch is ready
		self.dispatch_callback = dispatch_callback
		# Store the latest state
		self.latest_state = None
		
		print "SIM NEM initialised."
	
	# Adds a generator object to the list of generators.
	def add_generator(self, generator):
		# self.generators.append(generator)
		# bids is a dictthat stores a bid value for each generator
		# self.bidstack[generator.label] = None
		print "SIM Generator added", generator.label
	
	# Add a bid for this time period.
	def add_bid(self, gen_label, price, volume):
		print "SIM Adding bid", gen_label, price, volume
		# Add the bid
		self.bidstack[gen_label] = {'price':price, 'volume':volume}
		# Check if all bids have been submitted (ie. its time for dispatch)
		all_submitted = True
		for g in self.bidstack:
			# If we find that a generator hasn't yet submitted a bid set all_submitted to false.
			if not self.bidstack[g]:
				all_submitted = False
		# If all bids are submitted
		if all_submitted:
			self.dispatch()

	def MW_to_MWh(self, MW):
		return MW * (float(self.period_length_mins / 60.0))
	
	def MWh_to_MW(self, MWh):
		return MWh * (60.0 / float(self.period_length_mins))
	
	def dispatch(self):
		print "SIM Dispatching"
		demand = self.get_current_demand_MWh()
		# Convert bidstack dict to a list of dicts containing names and dicts.
		bids = [{'gen_label':gen_label, 'price': self.bidstack[gen_label]['price'], 'volume':self.bidstack[gen_label]['volume']} for gen_label in self.bidstack]
		# Sort the list of bids from smallest to largest price
		bids = sorted(bids, key=lambda bid: bid['price'])
		# Perform economic dispatch
		dispatch = {} #variable to store dispatch volume
		unmet_demand_MWh = demand #variable to store remaining unment demand
		price = -1000.0
		for bid in bids: #iterate through each bid in the bidstack
			amount_dispatch_requested = max(min(bid['volume'], unmet_demand_MWh),0) #calculate amount to requet from generator model
			required_generator_power_MW = self.MWh_to_MW(amount_dispatch_requested) #Calculate required power.
			amount_dispatched_MW = self.generators[bid['gen_label']].request_output_MW(required_generator_power_MW, self.period_length_mins) #Request that the gen dispatch at this power.
			dispatch[bid['gen_label']] = self.MW_to_MWh(amount_dispatched_MW) #record the generator's dispatch
			unmet_demand_MWh = max(unmet_demand_MWh - amount_dispatched_MW, 0) #recalc unmet demand
			price = bid['price']
		
		# Price floor
		price = max(0, price)
		# Price ceiling
		if price > 14200:
			price = 0

		print "Gen states:", [self.generators[g].current_output_MW for g in self.generators]
		self.latest_state = {
			'price':price,
			'unmet_demand_MWh':unmet_demand_MWh,
			'demand':demand,
			'next_demand':self.get_next_demand_MWh(),
			'dispatch':dispatch,
			'minimum_next_output_MWh':{label : g.get_minimum_next_output_MWh(self.period_length_mins) for label, g in self.generators.iteritems()}, #dict comprehension, see: https://www.datacamp.com/community/tutorials/python-dictionary-comprehension
			'maximum_next_output_MWh':{label : g.get_maximum_next_output_MWh(self.period_length_mins) for label, g in self.generators.iteritems()}, 
			'lrmc':{label : float(g.get_lrmc()) for label, g in self.generators.iteritems()}, 
			'srmc':{label : float(g.get_srmc()) for label, g in self.generators.iteritems()}, 
			'done':False,
			'fresh_reset':False,
			'bids':{b['gen_label']: b for b in bids},
		}
		
		# Reset the bidstack
		self.bidstack = {g : None for g in config.generators}
		# Step time forward by 1
		self.time_period += 1
		# Return the Dispatch object by passing it to the calback for emission via websockets.
		print "SIM Calling Dispatch Callback"
		self.dispatch_callback(self.latest_state)
		
		
	
	def reset(self, reset_callback):


		if not self.latest_state:
			self.latest_state = {
				'price':0,
				'unmet_demand_MWh':0,
				'demand':self.get_current_demand_MWh(),
				'next_demand':self.get_next_demand_MWh(),
				'dispatch': { label : 0 for label, g in self.generators.iteritems()},
				'minimum_next_output_MWh':{label : g.get_minimum_next_output_MWh(self.period_length_mins) for label, g in self.generators.iteritems()}, #dict comprehension, see: https://www.datacamp.com/community/tutorials/python-dictionary-comprehension
				'maximum_next_output_MWh':{label : g.get_maximum_next_output_MWh(self.period_length_mins) for label, g in self.generators.iteritems()}, 
				'lrmc':{label : float(g.get_lrmc()) for label, g in self.generators.iteritems()}, 
				'srmc':{label : float(g.get_srmc()) for label, g in self.generators.iteritems()}, 
				'done':False,
				'fresh_reset':True
			}
		
		# Call the callbacks to notify of a reset, 
		reset_callback(self.latest_state)
		# Also send a dispatch callback to provide a response to the next decision.
		# self.dispatch_callback(new_state)
	
	def get_current_demand_MWh(self):
		hour = float(self.time_period % 48) / 2
		if hour < 7 or hour > 18:
			return 80
		elif hour > 12 and hour < 16:
			return 120
		else:
			return 100
		
	def get_next_demand_MWh(self):
		
		next_period = self.time_period + 1
		next_hour = float(next_period % 48) / 2
		if next_hour < 7 or next_hour > 18:
			return 80
		elif next_hour > 12 and next_hour < 16:
			return 120
		else:
			return 100
	