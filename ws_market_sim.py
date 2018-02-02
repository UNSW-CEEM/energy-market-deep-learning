from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
import generators
import electricity_market


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


# Callback that notifies market participants of a dispatch event
def dispatched(result):
	# Contains details of generator dispatch
	print "SERVER Emitting Dispatch Message"
	emit('dispatched', result)
	
# Callback that notifies market participants of a dispatch event
def market_reset(result):
	# Contains details of generator dispatch
	print "SERVER Emitting RESET Message"
	emit('market_reset', result)
	

nem = electricity_market.Electricity_Market(dispatched, market_reset)


@socketio.on('message')
def handle_message(message):
	print('received message: ' + message)


@socketio.on('join_nem')
def join_nem(gen_label):
	# Create the generator object.
	generator = generators.Coal_Generator(
		label=gen_label, 
		capacity_MW = 1,
		ramp_rate_MW_per_min = 0.1,
		srmc = 40,
		lrmc = 40)
	# Add the generator to the nem.
	nem.add_generator(generator)
	emit('nem_joined', generator.label)


@socketio.on('add_bid')
def add_bid(bid):
	# Add the generator to the nem.
	print "adding bid", bid
	nem.add_bid(bid['gen_label'], bid['price'], bid['volume'])


@socketio.on('reset')
def reset():
	# Add the generator to the nem.
	nem.reset(market_reset)

@socketio.on('json')
def handle_json(json):
	print('received json: ' + str(json))
	print 'value', json['value']

@socketio.on('my event')
def handle_my_custom_event(json):
	print('received json: ' + str(json))
	print 'value', json['value']
	emit('my response', json)

if __name__ == '__main__':
	socketio.run(app)
