# Adapted from the ZMQ example code by Felipe Cruz <felipecruz@loogica.net> - released originally under the MIT/X11 License
import zmq
import sys
import threading
import time
from random import randint, random
from marketsim.simulations.simulation import Simulation
from marketsim.util.logging import tprint
import json






class ServerTask(threading.Thread):
    """ServerTask"""
    def __init__(self):
        threading.Thread.__init__ (self)

    def run(self):
        # Set up zero MQ frontend - this connects to clients
        context = zmq.Context()
        frontend = context.socket(zmq.ROUTER)
        frontend.bind('tcp://*:5570')
        # Set up zeromq backend - this connects to 
        backend = context.socket(zmq.DEALER)
        backend.bind('inproc://backend')
        # List of threads to process messages
        workers = []
        # Start a common electricity network/market simulation to be shared by all threads.
        simulation = Simulation()
        # Create the worker threads, pass them the simulations. There must be at least as many threads as participants.
        for i in range(len(simulation.participant_list)):
            worker = ServerWorker(context, simulation)
            worker.start()
            workers.append(worker)
        # Connect the workers to the incoming messages.
        zmq.proxy(frontend, backend)
        # Clean up when done.
        frontend.close()
        backend.close()
        context.term()

class ServerWorker(threading.Thread):
    """ServerWorker"""
    def __init__(self, context, simulation):
        threading.Thread.__init__ (self)
        self.context = context
        self.simulation = simulation
        self.sim_state = None
        # Event to signal that all bids are submitted and dispatch has occurred.
        self.dispatch_event = threading.Event()

    def run(self):
        """
            This function is called by each worker. 
            It's the 'main loop' for receiving/sending messages between bidders and the simulation.
        """
        # Connect the worker to zeroMQ
        worker = self.context.socket(zmq.DEALER)
        worker.connect('inproc://backend')
        tprint('Worker started', 101)
        
        # 'Main Loop'
        while True:
            # Clear the event, so it blocks on wait further down.
            self.dispatch_event.clear()
            # Receive a message via zeromq.
            ident, msg = worker.recv_multipart()
            data = json.loads(msg)
            # Add the received bid to the simulation.
            self.simulation.add_bid(data, self.callback)
            # Wait for all bids to be submitted and dispatch to occur (notified via callback below)
            self.dispatch_event.wait()
            # Send the simulation state as reply.
            reply = bytes(json.dumps(self.sim_state),'UTF-8')
            worker.send_multipart([ident, reply])
            
        worker.close()
    
    def callback(self, data):
        # Update the internal simulation state
        self.sim_state = data
        # Set the dispatch event, so that in the main loop it no longer blocks and sends the simulation state as a reply. 
        self.dispatch_event.set()
       

    
    
    


def main():
    """main function"""
    server = ServerTask()
    server.start()
  

    server.join()


if __name__ == "__main__":
    main()
