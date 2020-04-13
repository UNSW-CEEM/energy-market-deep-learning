import random


class Bid():
    """A bid that represents a price-quantity pair in the system."""
    def __init__(self, label, price, quantity, band):
        self.label = label
        # Add a random number here so that when bids are tied, the selection is truly random. 
        self.price = price + random.random()
        self.quantity = quantity
        self.band = band
    
    def copy(self):
        return Bid(self.label, self.price, self.quantity, self.band)
    
    def to_dict(self):
        return {
            'label':self.label,
            'price':self.price,
            'quantity':self.quantity,
            'band':self.band,
        }
    

class BidStack():
    """Provides an api that handles bidstack calculations."""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.stack = []
    
    def add_price_quantity_bid(self, bid_obj):
        """Adds a price <> quantity bid for a given participant."""
        self.stack.append( bid_obj )
    
    def economic_dispatch(self, capacity_MW):
        """Takes a capacity_MW and returns modified bids accepted under economic dispatch."""
        meritorder = sorted(self.stack, key=lambda k: k.price)
        accepted = []
        cumulative_cap_MW = 0
        # Loop through the sorted bids.
        for bid in meritorder:
            if cumulative_cap_MW + bid.quantity < capacity_MW:
                accepted.append(bid)
                cumulative_cap_MW += bid.quantity
            else:
                bid = bid.copy()
                bid.quantity = capacity_MW - cumulative_cap_MW
                accepted.append(bid)
                break
        return accepted

    def get_all_bids_dict(self):
        out = {}
        for bid in self.stack:
            label = bid.label
            out[label] = [] if not label in out else out[label]
            out[label].append(bid.to_dict())
        return out

class DispatchOrder():
    def __init__(self, winning_bids):
        self.winning_bids = winning_bids
    
    def get_generator_dispatch(self):
        dispatch = {}
        for bid in self.winning_bids:
            if not bid.label in dispatch:
                dispatch[bid.label] = 0
            dispatch[bid.label] += bid.quantity
        return dispatch

class Market():
    
    def __init__(self, participant_labels, dispatch_callback, initial_demand_MW):
        """ 
            Takes a list of participant labels (strings). 
            Also takes a dispatch callback, which is called when all bids are submitted.    
        """
        self.bidstack = BidStack()
        self.dispatch_callback = dispatch_callback
        self.timestep = 0
        self.participant_labels = participant_labels
        self.demand_MW = initial_demand_MW
        self.step(initial_demand_MW)
    
    def step(self, demand_MW):
        """Called to step the market forward in time by one. """
        self.timestep += 1
        self.submitted = { p : False for p in self.participant_labels }
        self.demand_MW = demand_MW
        self.bidstack = BidStack()
    
    def reset(self, demand_MW):
        self.timestep = 0
        self.step(demand_MW)
    
    def add_bid(self, participant_label, bids):
        """
            Takes a participant_label string, and an array of bid objects
        """
        self.submitted[participant_label] = True
        
        for bid in bids:
            self.bidstack.add_price_quantity_bid(bid)
        
        self.check_finished()

    def _get_state(self):

        # Perform economic dispatch to get a list of winning bids
        winning_bids = self.bidstack.economic_dispatch(self.demand_MW)
        
        # Generate a dispatch order object that stores a queriable result of the dispatch. 
        dispatch_order = DispatchOrder(winning_bids)
        
        # Calculate the market price - price of winning bid
        marginal_price = winning_bids[-1].price
        
        # Get a dict containing each gen and amount dispatched
        dispatch = dispatch_order.get_generator_dispatch()

        state = {
            'dispatch':dispatch,
            'price':marginal_price,
            'demand': self.demand_MW,
            'all_bids':self.bidstack.get_all_bids_dict()
        }
    
        return state
    
    def check_finished(self):
        """
            Checks whether all bids have been submitted. 
            If not, returns false.
            If so, calls the dispatch callback and returns true.
        """
        # Check if all have been submitted. 
        for participant_label in self.submitted:
            if not self.submitted[participant_label]:
                return False
        
        # If we get to here, it means all submitted. 
        # Get a dict to represent current market state.
        state = self._get_state()
        
        # Call the simulation's dispatch callback and pass it the market state.
        self.dispatch_callback(state)
        return True

    