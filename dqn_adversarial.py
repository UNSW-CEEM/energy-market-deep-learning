import numpy as np
import gym

import marketsim.openai.envs

from marketsim.logbook.logbook import logbook

from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from keras.optimizers import Adam

import tensorflow as tf
from keras import backend as K

from rl.agents.dqn import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory

import pendulum

import sys

import space_wrappers


notes = """
Adversarial network. 
First go, with deterministic and oscillating (and repeating) demand looked hopeful. 
I'm not an advanced enough intelligence to know whether it's sensible though. 
This run will thus have one change:
- Demand will be pseudo-random, between max and min.

"""

possible_participants = ['Nyngan', 'Bayswater']

# Make sure that a participant name is provided.
if len(sys.argv) < 2:
    print('Error: Participant name not provided - usage: python dqn_adversarial.py <participant_name>')
    print('Possible participant names:')
    [print(" -"+p) for p in possible_participants]
    sys.exit()
# Make sure that the participant name is one of hte allowed ones. 
elif sys.argv[1] not in possible_participants:
    print('Error: Participant not in list of possible participants. Must be one of:')
    [print(" -"+p) for p in possible_participants]
    sys.exit()
else:
    participant_name = sys.argv[1]



# ENV_NAME = 'CartPole-v0'
ENV_NAME = 'MultiBidMarket-v0'
extra_label = "Simple Adversarial"

logbook().set_label(extra_label+" "+ENV_NAME+" "+participant_name+" "+pendulum.now().format('D/M HH:mm'))
logbook().record_metadata('Environment', ENV_NAME)
logbook().record_metadata('datetime', pendulum.now().isoformat())



# Set the tensorflow memory growth to auto - this is important when running two simultaneous models
# Otherwise, the first process hogs all the memory and the second (the one that we watch the output of)
# gets a CUDA_ERROR_OUT_OF_MEMORY message and crashes.
config = tf.ConfigProto()
# config.gpu_options.allow_growth = True #Set automatically - takes some time. 
config.gpu_options.per_process_gpu_memory_fraction = 0.95 / float(len(possible_participants)) # Alternatively, allocate as a fraction of the available memory:
sess = tf.Session(config=config)
K.set_session(sess)


# Get the environment and extract the number of actions.
env = gym.make(ENV_NAME)
# Wrap so that we have a discrete action space - maps the internal MultiDiscrete action space to a Discrete action space.
env = space_wrappers.FlattenedActionWrapper(env)
env.connect(participant_name, possible_participants.index(participant_name))
np.random.seed(123)
env.seed(123)
nb_actions = env.action_space.n #use this one if Discrete action space
# nb_actions = env.action_space.shape[0] # use this one if Box action space
logbook().record_hyperparameter('action_space', str(env.action_space))
logbook().record_hyperparameter('action_space_size', str(nb_actions))

# Next, we build a very simple model.
model = Sequential()
model.add(Flatten(input_shape=(1,) + env.observation_space.shape))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(nb_actions))
model.add(Activation('linear'))
print("MODEL SUMMARY",model.summary())

logbook().record_model_json(model.to_json())


# Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
# even the metrics!
memory = SequentialMemory(limit=50000, window_length=1)
policy = BoltzmannQPolicy()

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
# learning_rate = 1e-6
learning_rate = 1e-3
dqn.compile(Adam(lr=learning_rate), metrics=['mae'])
logbook().record_hyperparameter('Learning Rate', learning_rate)

# Okay, now it's time to learn something! We visualize the training here for show, but this
# slows down training quite a lot. You can always safely abort the training prematurely using
# Ctrl + C.
# dqn.fit(env, nb_steps=50000, visualize=False, verbose=2)
# nb_steps = 500000
nb_steps = 50000
# nb_steps = 50
dqn.fit(env, nb_steps=nb_steps, visualize=False, verbose=2)
logbook().record_hyperparameter('nb_steps', nb_steps)

# After training is done, we save the final weights.
dqn.save_weights('dqn_{}_weights.h5f'.format(ENV_NAME), overwrite=True)

# Finally, evaluate our algorithm for 5 episodes.
nb_episodes = 5
logbook().record_metadata('nb_episodes (testing)', nb_episodes)
dqn.test(env, nb_episodes=5, visualize=True)



logbook().record_notes(notes)
logbook().submit()
