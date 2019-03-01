# Adapted from the ZMQ example code by Felipe Cruz <felipecruz@loogica.net> - released originally under the MIT/X11 License

import zmq
import sys

from random import randint, random
import threading

import json
import time
from ...util.logging import tprint

labels = ['Nyngan', 'Bayswater', 'Moree']

class ClientTask():
    """ClientTask"""
    def __init__(self, id):
        self.id = id

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.DEALER)
        identity = u'worker-%d' % self.id
        socket.identity = identity.encode('ascii')
        socket.connect('tcp://localhost:5570')
        tprint('Client %s started' % (identity),color=self.id+1)
        poll = zmq.Poller()
        poll.register(socket, zmq.POLLIN)
        reqs = 0
        while True:
            reqs = reqs + 1
            tprint(str(self.id)+'Req #%d sent..' % (reqs),color=self.id+1)
            # Dummy Bid Data
            data = {
                'id': self.id,
                'label':labels[self.id],
                'bids' : [
                    [10,1],
                    [20,1],
                    [30,1],
                    [40,1],
                    [50,1],
                ],
            }

            data_str = json.dumps(data)
            socket.send_string(data_str)

            # socket.send_string(u'request #%d' % (reqs))
            for i in range(5):
                tprint("Polling Attempt: "+str(i), color=self.id+1)
                sockets = dict(poll.poll(1000))
                if socket in sockets:
                    msg = socket.recv()
                    tprint('Client %s received: %s' % (identity, msg),color=self.id+1)
                    # For testing purposes - otherwise you'll do about a thousand a second. 
                    time.sleep(1)
                    break

        socket.close()
        context.term()

def main():
    """main function"""
    
    for i in range(10):
        client = ClientTask(i)
        client.start()


if __name__ == "__main__":
    # Runs a multithreaded test set of clients. Not suitable for tensorflow - testing only. 
    for i in range(3):
        client = ClientTask(i)
        t = threading.Thread(target=client.run)
        t.start()
        
