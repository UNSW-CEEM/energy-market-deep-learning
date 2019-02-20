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
        context = zmq.Context()
        frontend = context.socket(zmq.ROUTER)
        frontend.bind('tcp://*:5570')

        backend = context.socket(zmq.DEALER)
        backend.bind('inproc://backend')

        workers = []

        simulation = Simulation()

        for i in range(5):
            worker = ServerWorker(context, simulation)
            worker.start()
            workers.append(worker)

        zmq.proxy(frontend, backend)

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
        self.event = threading.Event()

    def run(self):
        worker = self.context.socket(zmq.DEALER)
        worker.connect('inproc://backend')
        tprint('Worker started', 101)
        
        while True:
            # Clear the event, so it blocks on wait.
            self.event.clear()
            
            ident, msg = worker.recv_multipart()
            # tprint('Worker received %s from %s' % (msg, ident), 200)
            data = json.loads(msg)
            self.simulation.add_bid(data, self.callback)
            # Wait for the data callback
            self.event.wait()
            reply = bytes(json.dumps(self.sim_state),'UTF-8')
            # worker.send_multipart([ident, msg])
            worker.send_multipart([ident, reply])
            # worker.send_multipart([ident, self.sim_state])

        worker.close()
    
    def callback(self, data):
        self.sim_state = data
        # Set the event, so wait()
        self.event.set()
        # self.worker.send_multipart([ident, msg])
        # Unlock

    
    
    


def main():
    """main function"""
    server = ServerTask()
    server.start()
  

    server.join()


if __name__ == "__main__":
    main()
