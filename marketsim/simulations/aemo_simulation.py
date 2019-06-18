from marketsim.model.generator import Generator
from marketsim.model.energy_market import Market, Bid
from marketsim.model.demand import Demand, RandomDemand, RandomDiscreteDemand
from aemo_config import params
import pendulum


# Jenga Stuff
from mongoengine import connect
connect(params['DB_NAME'],
    host=params['MONGO_HOST'],
    username=params['MONGO_USER'],
    password=params['MONGO_PASSWORD'],
    authentication_source=params['MONGO_AUTH_SOURCE']
)

from marketsim.jenga_service.participants import ParticipantService
from marketsim.jenga_service.bidstack import get_bids
from marketsim.jenga_service.demand import get_demand
participant_service = ParticipantService()

import inspect
from ..util.logging import tprint
from threading import Lock

import os


demand_path = os.path.join('data', 'input', 'PRICE_AND_DEMAND_201901_TAS1.csv')

class AEMOSimulation():
    """
        A simulation defines the way in which an electricity market is set up. 
        Additionally it provides an external API for interacting with a simulation.
        This object provides a minimal implementation and example of the simulation api. 
        This api can then be used as a standalone package, or linked to a server (ie http/ws/zmq)
        Simulations are designed to be threadsafe.
    """
    def __init__(self):
        # self.market = Market()
        print("AEMO Simulation Initialised")
        self.callbacks = []
        self.lock = Lock()

        self.aemo_state = ["NSW", "QLD", "SA", "VIC", "TAS"][0]

        self.loop_start_date = pendulum.datetime(2018,6,5)
        self.loop_end_date = pendulum.datetime(2018,6,5)
        self.current_date = self.loop_start_date

        # List of market participants connecting via zmq.
        self.agent_list = params['PARTICIPANTS']
        # List of all market participants in the simulation
        self.aemo_participant_list = participant_service.get_participant_list(self.aemo_state)
        self.participant_list = self.agent_list + self.aemo_participant_list
        
        print("Participants",self.participant_list)
        # Object that returns next demand in series. 
        # self.demand = Demand(demand_path)
        demand = get_demand(self.aemo_state, self.current_date)
        # Object that simulates an electricity market
        self.market = Market(self.participant_list, self.dispatch_callback, demand)
        self.add_non_agent_bids(self.current_date)
        

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
        self.current_date = self.current_date.add(minutes=30) if self.current_date.add(minutes=30) < self.loop_end_date else self.loop_start_date
        next_demand = get_demand(self.aemo_state, self.current_date)

        
        # Callback 
        for c in self.callbacks:
            market_state['next_demand'] = next_demand
            c(market_state)
        self.callbacks = []

        # Update the date in the date loop (reset to beginning of loop if )
        
        # Step the market to the next demand level.
        
        self.market.step(demand_MW = next_demand)

        # Add the bids for the non-agent-based bidders.
        self.add_non_agent_bids(self.current_date)

    def add_non_agent_bids(self, dt):
        print("Adding Non-Agent Bids")
        jenga_bidstack_data = get_bids(self.aemo_participant_list, dt)
        for participant_label in self.aemo_participant_list:
            bids = []
            if participant_label in jenga_bidstack_data:
                for band in jenga_bidstack_data[participant_label]['bands']:
                    price = jenga_bidstack_data[participant_label]['bands'][band]['price']
                    volume = jenga_bidstack_data[participant_label]['bands'][band]['volume']
                    if volume > 0:
                        # Assemble a bid object from the data.
                        b = Bid(label=participant_label, price=price, quantity = volume, band=int(band))
                        bids.append(b)
            self.market.add_bid(participant_label = participant_label, bids = bids)

        # print(bids)


class SimulationFactory():
    
    def get_simulation(scenario_type):
        return Simulation()