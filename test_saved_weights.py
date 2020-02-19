import numpy as np
import gym

import marketsim.openai.envs

from marketsim.logbook.logbook import logbook

from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten, LSTM
from keras.optimizers import Adam

import tensorflow as tf
from keras import backend as K

from rl.agents.dqn import DQNAgent
from rl.policy import BoltzmannQPolicy, MaxBoltzmannQPolicy, GreedyQPolicy, EpsGreedyQPolicy, BoltzmannGumbelQPolicy
from rl.memory import SequentialMemory

import pendulum

import sys

import space_wrappers

from market_config import params as market_config

notes = """
    From saved weights on failed model (due to ram) at the 3 million mark. Testing weights. Details below.

    Kicking off a giant. 
    7 million. 

    Trying out the model from a DQN market trading example. 
    Trying to run all on one again.

    5 Prices

    Learning Rate 1e-2
    
    Took max demand to 10 not 20, lower obs space. 
    Evolving demand. Signalling next demand. No guidance on previous bids under these conditions (because superflous) BUT
    shouwing previous bids. The idea here is that the equilibrium might come out to be that for any given demand, over a number of rounds, participants adjust their bids
    such that demand is split between them, and price is maximised.
    
    EPS-Greedy Policy.
    
    5 bands each.
"""


# Make sure that a participant name is provided.
if len(sys.argv) < 3:
    print('Error: Participant name and file name not provided - usage: python dqn_adversarial.py <participant_name> <weight_file>')
    print('Possible participant names:')
    [print(" -"+p) for p in market_config['PARTICIPANTS']]
    sys.exit()
# Make sure that the participant name is one of hte allowed ones. 
elif sys.argv[1] not in market_config['PARTICIPANTS']:
    print('Error: Participant not in list of possible participants. Must be one of:')
    [print(" -"+p) for p in market_config['PARTICIPANTS']]
    sys.exit()
else:
    participant_name = sys.argv[1]
    file_path = sys.argv[2]



# ENV_NAME = 'CartPole-v0'
# ENV_NAME = 'MultiBidMarket-v0'
ENV_NAME = 'MultiBidMarketEfficient-v0'
extra_label = "Simple Adversarial"

logbook().set_label(extra_label+" "+ENV_NAME+" "+participant_name+" "+pendulum.now().format('D/M HH:mm'))
logbook().record_metadata('Environment', ENV_NAME)
logbook().record_metadata('datetime', pendulum.now().isoformat())
for param in market_config:
    logbook().record_metadata('Market: '+param, market_config[param])



# Set the tensorflow memory growth to auto - this is important when running two simultaneous models
# Otherwise, the first process hogs all the memory and the second (the one that we watch the output of)
# gets a CUDA_ERROR_OUT_OF_MEMORY message and crashes.
config = tf.ConfigProto()
# config.gpu_options.allow_growth = True #Set automatically - takes some time. 
config.gpu_options.per_process_gpu_memory_fraction = 0.95 / float(len(market_config['PARTICIPANTS'])) # Alternatively, allocate as a fraction of the available memory:
sess = tf.Session(config=config)
K.set_session(sess)

# Get the environment and extract the number of actions.
env = gym.make(ENV_NAME)
# Wrap so that we have a discrete action space - maps the internal MultiDiscrete action space to a Discrete action space.
env = space_wrappers.FlattenedActionWrapper(env)
env.connect(participant_name, market_config['PARTICIPANTS'].index(participant_name))
np.random.seed(123)
env.seed(123)
nb_actions = env.action_space.n #use this one if Discrete action space
# nb_actions = env.action_space.shape[0] # use this one if Box action space
logbook().record_hyperparameter('action_space', str(env.action_space))
logbook().record_hyperparameter('action_space_size', str(nb_actions))

# Next, we build a very simple model.
# This is a model based on the Atari demo.
# model = Sequential()
# model.add(Flatten(input_shape=(1,) + env.observation_space.shape))
# model.add(Dense(16))
# model.add(Activation('relu'))
# model.add(Dense(16))
# model.add(Activation('relu'))
# model.add(Dense(16))
# model.add(Activation('relu'))
# model.add(Dense(nb_actions))
# model.add(Activation('linear'))

# This is a model based on Deep RL Trader by miroblog (https://github.com/miroblog/deep_rl_trader)
model = Sequential()
model.add(LSTM(64, input_shape=(1,) + env.observation_space.shape, return_sequences=True))
model.add(LSTM(64))
model.add(Dense(32))
model.add(Activation('relu'))
model.add(Dense(nb_actions, activation='linear'))


# Record details of the model.
print("MODEL SUMMARY",model.summary())
logbook().record_model_json(model.to_json())

# Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
# even the metrics!
memory = SequentialMemory(limit=50000, window_length=1) # see https://stackoverflow.com/questions/47140642/what-does-the-episodeparametermemory-of-keras-rl-do
# policy = BoltzmannQPolicy()
# policy = MaxBoltzmannQPolicy()
# policy = GreedyQPolicy()
policy = EpsGreedyQPolicy()
# policy = BoltzmannGumbelQPolicy()

# DQN Agent Source here: https://github.com/keras-rl/keras-rl/blob/master/rl/agents/dqn.py#L89
dqn = DQNAgent(model=model, nb_actions=nb_actions, memory=memory, nb_steps_warmup=10000, target_model_update=1e-3, policy=policy)
# Record to logbook
logbook().record_hyperparameter('Agent', str(type(dqn)))
logbook().record_hyperparameter('Memory Type', str(type(memory)))
logbook().record_hyperparameter('Memory Limit', memory.limit)
logbook().record_hyperparameter('Memory Window Length', memory.window_length)
logbook().record_hyperparameter('nb_steps_warmup', dqn.nb_steps_warmup) #info on this parameter here: https://datascience.stackexchange.com/questions/46056/in-keras-library-what-is-the-meaning-of-nb-steps-warmup-in-the-dqnagent-objec
logbook().record_hyperparameter('target_model_update', dqn.target_model_update) #info on this parameter here: https://github.com/keras-rl/keras-rl/issues/55
logbook().record_hyperparameter('nb_actions', nb_actions)
logbook().record_hyperparameter('batch_size', dqn.batch_size) #defaults to 32. Info here: https://radiopaedia.org/articles/batch-size-machine-learning
logbook().record_hyperparameter('gamma', dqn.gamma) #defaults to 0.99. 'Discount rate' according to Advanced Deep Learning with Keras


# dqn.compile(Adam(lr=1e-3), metrics=['mae'])
# Needs general tuning, usually model-specific - https://machinelearningmastery.com/learning-rate-for-deep-learning-neural-networks/
# learning_rate = 1e-6
# learning_rate = 1e-3
# learning_rate = 1e-3
learning_rate = 1e-2
# learning_rate = 1e-1
dqn.compile(Adam(lr=learning_rate), metrics=['mae'])
logbook().record_hyperparameter('Learning Rate', learning_rate)


logbook().record_hyperparameter('nb_steps', 0)

# After training is done, we save the final weights.
dqn.load_weights(file_path)

# Finally, evaluate our algorithm for 5 episodes.
nb_episodes = 20
logbook().record_metadata('nb_episodes (testing)', nb_episodes)
dqn.test(env, nb_episodes=5, visualize=True)

logbook().record_notes(notes)

logbook().save_json()
logbook().trim()
logbook().submit()
