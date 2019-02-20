

#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#

import time
import zmq
import json

class Server():
    def __init__(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")
    
    def run(self):
        while True:
            #  Wait for next request from client
            message = self.socket.recv()
            message2 = self.socket.recv()
            print("Received request: %s" % message)
            data = json.loads(message)

            #  Do some 'work'
            time.sleep(1)

            #  Send reply back to client
            self.socket.send_string("Your Generator ID was %s" % data['id'])

    

if __name__ == "__main__":
    s = Server()
    s.run()
