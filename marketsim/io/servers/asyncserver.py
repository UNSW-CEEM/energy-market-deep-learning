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

    def run(self):
        worker = self.context.socket(zmq.DEALER)
        worker.connect('inproc://backend')
        tprint('Worker started', 101)
        while True:
            ident, msg = worker.recv_multipart()
            tprint('Worker received %s from %s' % (msg, ident))
            data = json.loads(msg)
            self.simulation.add_bid(data)
            replies = randint(0,4)
            for i in range(replies):
                # time.sleep(0.1)
                worker.send_multipart([ident, msg])

        worker.close()
    


def main():
    """main function"""
    server = ServerTask()
    server.start()
  

    server.join()


if __name__ == "__main__":
    main()
