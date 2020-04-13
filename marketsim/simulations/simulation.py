from marketsim.model.generator import Generator
from marketsim.model.energy_market import Market, Bid
from marketsim.model.demand import Demand, RandomDemand, RandomDiscreteDemand, FixedDemand, EvolvingDemand
import market_config
import inspect
from ..util.logging import tprint
from threading import Lock

import os


demand_path = os.path.join('data', 'input', 'PRICE_AND_DEMAND_201901_TAS1.csv')

class Simulation():
    """
        A simulation defines the way in which an electricity market is set up. 
        Additionally it provides an external API for interacting with a simulation.
        This object provides a minimal implementation and example of the simulation api. 
        This api can then be used as a standalone package, or linked to a server (ie http/ws/zmq)
        Simulations are designed to be threadsafe.
    """
    def __init__(self):
        # self.market = Market()
        print("Simulation Initialised")
        self.callbacks = []
        self.lock = Lock()

        # List of participants
        self.participant_list = market_config.params['PARTICIPANTS']
        # Object that returns next demand in series. 
        if market_config.params['DEMAND_TYPE'] == 'fixed':
            self.demand = FixedDemand()
        elif market_config.params['DEMAND_TYPE'] == 'evolving':
            self.demand = EvolvingDemand(probability = 0.1)
        else:
            self.demand = RandomDiscreteDemand()
        # Object that simulates an electricity market
        self.market = Market(self.participant_list, self.dispatch_callback, self.demand.next())
        

    def add_generator(self, label, type, nameplate_MW):
        """Add a generator to the simulation."""
        g = Generator(nameplate_MW)
    
    def add_bid(self, bid_data, callback):
        """
            Takes a python dict full of bid data.  
        """
        with self.lock:
            self.callbacks.append(callback)
            
            tprint("Bid Added:"+str(bid_data), color= bid_data['id']+1)
            bids = []

            for band, bid in enumerate(bid_data['bids']):
                # Assemble a bid object from the data.
                b = Bid(label=bid_data['label'], price=bid[0], quantity = bid[1], band=band)
                bids.append(b)
            self.market.add_bid(participant_label = bid_data['label'], bids = bids)
    
    def dispatch_callback(self, market_state):
        tprint("Sending Callbacks", 210)
        next_demand = self.demand.next()
        for c in self.callbacks:
            market_state['next_demand'] = next_demand
            c(market_state)
        self.callbacks = []

        self.market.step(demand_MW = next_demand)

class SimulationFactory():
    
    def get_simulation(scenario_type):
        return Simulation()