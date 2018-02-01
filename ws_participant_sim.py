# From docs at https://pypi.python.org/pypi/socketIO-client

import logging


from socketIO_client import SocketIO, LoggingNamespace, BaseNamespace, SocketIONamespace
import time
# # This defines a set of functions that are used by websockets.
# class ParticipantNamespace(BaseNamespace):
# 	def on_nem_joined(self, *args):
# 		print "PARTICIPANT", "NEM Successfully Joined"

# 	def on_dispatched(self, *args):
# 		print "PARTICIPANT", "Recieved Dispatch Message:"
	
	
# 	# Sets the participant object, so that commands via websocket can call participant functions.
# 	def set_participant(self, participant):
# 		self.participant = participant




# Uses websockets to talk to the market sim server
# And also implements the OpenAI interface for talking to OpenAI Gym
class Single_Ownership_Participant_Interface():
	def __init__(self, market, gen_name):
		self.market = market
		self.gen_name = gen_name
		self.socketIO = SocketIO('localhost', 5000, BaseNamespace)
		# self.socketIO.get_namespace().set_participant(self)
		self.socketIO.on('dispatched', self.dispatch)
		# Request to join the nem
		self.socketIO.emit('join_nem', gen_name)
		self.socketIO.wait(seconds=3)
	
	def dispatch(self, result):
		print "PARTICIPANT", "Dispatched", result

	# def seed(self, seed=None):
	# 	return self.market._seed(seed)
	# def step(self, action):
	# 	return self.market.step(action, self.label)
	# def reset(self):
	# 	return self.market._reset()
	# def render(self, mode='human', close=False):
	# 	return self.market._render(mode=mode, close=close)

	def add_bid(self, price, volume):
		self.socketIO.emit('add_bid', {'gen_label':self.gen_name, 'price':float(price), 'volume':float(volume) })
		print "PARTICIPANT", "Emitted, waiting 5 secs."
		self.socketIO.wait()
		# time.sleep(5)
		

if __name__ == "__main__":
	logging.getLogger('socketIO-client').setLevel(logging.DEBUG)
	logging.basicConfig()

	participant = Single_Ownership_Participant_Interface('nem', 'Eraring')
	participant.add_bid(30, 50.5)
	
