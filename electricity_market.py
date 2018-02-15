# An events-based electricity market simulator.

class Electricity_Market():
	# Called when a new electricity market object is created. 
	def __init__(self, dispatch_callback):
		# Keep track of the current time period. 
		self.time_period = 0
		# Store the number of minutes per time period
		self.period_length_mins = 30
		# generators is a list of generator objects.
		self.generators = []
		# bids is a dictthat stores a bid value for each generator
		self.bidstack = {}
		# Function that is called when dispatch is ready
		self.dispatch_callback = dispatch_callback
		# Store the latest state
		self.latest_state = None
		
		print "SIM NEM initialised."
	
	# Adds a generator object to the list of generators.
	def add_generator(self, generator):
		self.generators.append(generator)
		# bids is a dictthat stores a bid value for each generator
		self.bidstack[generator.label] = None
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
	
	def dispatch(self):
		print "SIM Dispatching"
		demand = self.get_current_demand()
		# Convert bidstack dict to a list of dicts containing names and dicts.
		bids = [{'gen_label':gen_label, 'price':self.bidstack[gen_label]['price'], 'volume':self.bidstack[gen_label]['volume']} for gen_label in self.bidstack]
		# Sort the list of bids from smallest to largest price
		bids = sorted(bids, key=lambda bid: bid['price'])
		# Perform economic dispatch
		dispatch = {} #variable to store dispatch volume
		unmet_demand = demand #variable to store remaining unment demand
		price = -1000.0
		for bid in bids: #iterate through each bid in the bidstack
			amount_dispatched = min(bid['volume'], unmet_demand) #calculate amount dispatched
			dispatch[bid['gen_label']] = amount_dispatched #record the generator's dispatch
			unmet_demand = max(unmet_demand - amount_dispatched, 0) #recalc unmet demand
			price = bid['price']
		# Return the Dispatch object by passing it to the calback for emission via websockets.
		print "SIM Calling Dispatch Callback"

		self.latest_state = {
			'price':price,
			'unmet_demand':unmet_demand,
			'demand':demand,
			'next_demand':self.get_next_demand(),
			'dispatch':dispatch,
			'minimum_next_output_MWh':{g.label : g.get_minimum_next_output_MWh(self.period_length_mins) for g in self.generators}, #dict comprehension, see: https://www.datacamp.com/community/tutorials/python-dictionary-comprehension
			'maximum_next_output_MWh':{g.label : g.get_maximum_next_output_MWh(self.period_length_mins) for g in self.generators}, 
			'lrmc':{g.label : float(g.get_lrmc()) for g in self.generators}, 
			'srmc':{g.label : float(g.get_srmc()) for g in self.generators}, 
			'done':False,
			'fresh_reset':False,
		}
		
		self.dispatch_callback(self.latest_state)
	
	def reset(self, reset_callback):
		

		if not self.latest_state:
			self.latest_state = {
				'price':0,
				'unmet_demand':0,
				'demand':self.get_current_demand(),
				'next_demand':self.get_next_demand(),
				'dispatch': { g.label : 0 for g in self.generators},
				'minimum_next_output_MWh':{g.label : g.get_minimum_next_output_MWh(self.period_length_mins) for g in self.generators}, #dict comprehension, see: https://www.datacamp.com/community/tutorials/python-dictionary-comprehension
				'maximum_next_output_MWh':{g.label : g.get_maximum_next_output_MWh(self.period_length_mins) for g in self.generators}, 
				'lrmc':{g.label : float(g.get_lrmc()) for g in self.generators}, 
				'srmc':{g.label : float(g.get_srmc()) for g in self.generators}, 
				'done':False,
				'fresh_reset':True
			}
		
		# Call the callbacks to notify of a reset, 
		reset_callback(self.latest_state)
		# Also send a dispatch callback to provide a response to the next decision.
		# self.dispatch_callback(new_state)
	
	def get_current_demand(self):
		return 100

	def get_next_demand(self):
		return 100
	