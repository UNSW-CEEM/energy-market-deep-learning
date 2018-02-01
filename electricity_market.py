# An events-based electricity market simulator.

class Electricity_Market():
	# Called when a new electricity market object is created. 
	def __init__(self, dispatch_callback):
		# Keep track of the current time period. 
		self.time_period = 0
		# generators is a list of generator objects.
		self.generators = []
		# bids is a dictthat stores a bid value for each generator
		self.bidstack = {}
		# Function that is called when dispatch is ready
		self.dispatch_callback = dispatch_callback
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

		print "SIM Calling Dispatch Callback"
		self.dispatch_callback({
			'price':price,
			'unmet_demand':unmet_demand,
			'demand':demand,
			'dispatch':dispatch
		})
	
	def get_current_demand(self):
		return 10
	