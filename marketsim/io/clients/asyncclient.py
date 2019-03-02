# Adapted from the ZMQ example code by Felipe Cruz <felipecruz@loogica.net> - released originally under the MIT/X11 License

import zmq
import sys

from random import randint, random
import threading

import json
import time
from ...util.logging import tprint

# labels = ['Nyngan', 'Bayswater', 'Moree']
# labels = ['Nyngan', 'Bayswater']
labels = ['Nyngan']

class AsyncClient():
    """AsyncClient"""
    def __init__(self, id):
        self.id = id
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.identity = u'worker-%d' % self.id
        self.socket.identity = self.identity.encode('ascii')
        self.socket.connect('tcp://localhost:5570')
        tprint('Client %s started' % (self.identity),color=self.id+1)
        self.poll = zmq.Poller()
        self.poll.register(self.socket, zmq.POLLIN)
        self.reqs = 0

    def send(self, data):
        """ Sends data to the server. Returns the reply."""
        data_str = json.dumps(data)
        self.socket.send_string(data_str)

        self.reqs = self.reqs + 1
        # tprint(str(self.id)+' Req #%d sent..' % (self.reqs),color=self.id+1)


        # Receive Reply
        # Wait for reply.
        # for i in range(5):
        i = 0
        while True:
            i+= 1
            # tprint("Polling Attempt: "+str(i), color=self.id+1)
            sockets = dict(self.poll.poll(1000))
            if self.socket in sockets:
                msg = self.socket.recv()
                # tprint('Client %s received: %s' % (self.identity, msg),color=self.id+1)
                # For testing purposes - otherwise you'll do about a thousand a second. 
                # time.sleep(1)
                break
        return json.loads(msg)
    
    def close(self):
        self.socket.close()
        self.context.term()

        

    def loop(self):
        
        reqs = 0
        while True:
            
            # Dummy Bid Data
            data = {
                'id': self.id,
                'label':labels[self.id],
                'bids' : [
                    [10,1000],
                    [100,1000],
                ],
            }

            self.send(data)

        self.close()

def main():
    """main function"""
    
    for i in range(10):
        client = AsyncClient(i)
        client.start()


if __name__ == "__main__":
    # Runs a multithreaded test set of clients. Not suitable for tensorflow - testing only. 
    for i in range(len(labels)):
        client = AsyncClient(i)
        t = threading.Thread(target=client.loop)
        t.start()
        
