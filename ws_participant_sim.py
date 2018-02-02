# From docs at https://pypi.python.org/pypi/socketIO-client

import logging


from socketIO_client import SocketIO, LoggingNamespace, BaseNamespace, SocketIONamespace
import time
import threading
import sys
# # This defines a set of functions that are used by websockets.
# class ParticipantNamespace(BaseNamespace):
# 	def on_nem_joined(self, *args):
# 		print "WS", "NEM Successfully Joined"

# 	def on_dispatched(self, *args):
# 		print "WS", "Recieved Dispatch Message:"
	
	
# 	# Sets the participant object, so that commands via websocket can call participant functions.
# 	def set_participant(self, participant):
# 		self.participant = participant




# Uses websockets to talk to the market sim server
# And also implements the OpenAI interface for talking to OpenAI Gym
class Single_Ownership_Participant():
	def __init__(self, gen_name, dispatch_callback, reset_callback):
		print "Initialising Single Ownership Participant"
		self.dispatch_callback = dispatch_callback
		self.reset_callback = reset_callback
		self.gen_name = gen_name
		self.socketIO = SocketIO('localhost', 5000, BaseNamespace)
		# self.socketIO.get_namespace().set_participant(self)
		self.socketIO.on('dispatched', self.dispatch)
		self.socketIO.on('market_reset', self.reset_callback)
		# Request to join the nem
		self.socketIO.emit('join_nem', gen_name)

		# Always be listening in the background.
		t = threading.Thread(target=self.socketIO.wait)
		t.daemon = True # this line enables ctrl+c exit of the thread
		t.start()
	
	def dispatch(self, result):
		print "WS", "Dispatched", result
		self.dispatch_callback(result)

	def add_bid(self, price, volume):
		self.socketIO.emit('add_bid', {'gen_label':self.gen_name, 'price':float(price), 'volume':float(volume) })
		# self.socketIO.wait(1)
		# print "WS", "Emitted, waiting 5 secs."
		# self.socketIO.wait()
		# time.sleep(5)
	
	def reset(self):
		print "WS", "Resetting..."
		self.socketIO.emit('reset')
	
		

if __name__ == "__main__":
	def dispatch_callback(result):
		print "Dispatch Callback:", result

	logging.getLogger('socketIO-client').setLevel(logging.DEBUG)
	logging.basicConfig()

	participant = Single_Ownership_Participant('Eraring', dispatch_callback)
	participant.add_bid(30, 50.5)
	
