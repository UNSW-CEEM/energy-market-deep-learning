from marketsim.model.generator import Generator
from marketsim.model.energy_market import Market

from ..util.logging import tprint

class Simulation():
    """
        A simulation defines the way in which an electricity market is set up. 
        This object provides a minimal implementation and example of the simulation api. 
        This api can then be used as a standalone package, or linked to a server (ie http/ws/zmq)
        Simulations are designed to be threadsafe.
    """
    def __init__(self):
        # self.market = Market()
        print("Simulation Initialised")
        

    def add_generator(self, label, type, nameplate_MW):
        """Add a generator to the simulation."""
        g = Generator(nameplate_MW)
    
    def add_bid(self, bid, callback):
        tprint("Bid Added:"+str(bid), color= bid['id']+1)
        callback({'success':True})

    
        

class SimulationFactory():
    
    def get_simulation(scenario_type):
        return Simulation()