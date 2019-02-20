from .model.generator import Generator
from .model.energy_market import Market

class Simulation():
    """
        A simulation defines the way in which an electricity market is set up. 
        This object provides a minimal implementation and example of the simulation api. 
        This api can then be used as a standalone package, or linked to a server (ie http/ws/zmq)
    """
    def __init__():
        self.market = Market()

    def add_generator(label, type, nameplate_MW):
        """Add a generator to the simulation."""
        g = Generator(nameplate_MW)
    

    def run():
        

class SimulationFactory():
    
    def get_simulation(scenario_type):
        return Simulation()