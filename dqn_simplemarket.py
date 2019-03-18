import numpy as np
import gym

import marketsim.openai.envs

from marketsim.logbook.logbook import logbook

from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from keras.optimizers import Adam

from rl.agents.dqn import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory

import pendulum

# ENV_NAME = 'CartPole-v0'
ENV_NAME = 'SimpleMarket-v0'
extra_label = "Simple Shadow"

logbook().set_label(extra_label+" "+ENV_NAME+" "+pendulum.now().format('ddd D/M HH:mm'))
logbook().record_metadata('Environment', ENV_NAME)

# Get the environment and extract the number of actions.
env = gym.make(ENV_NAME)
np.random.seed(123)
env.seed(123)
nb_actions = env.action_space.n

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

logbook().record_metadata('Model Summary', str(model.summary()))


# Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
# even the metrics!
memory = SequentialMemory(limit=50000, window_length=1)
policy = BoltzmannQPolicy()
dqn = DQNAgent(model=model, nb_actions=nb_actions, memory=memory, nb_steps_warmup=10, target_model_update=1e-2, policy=policy, )
# Record to logbook
logbook().record_hyperparameter('Agent', str(type(dqn)))
logbook().record_hyperparameter('Memory Type', str(type(memory)))
logbook().record_hyperparameter('Memory Limit', memory.limit)
logbook().record_hyperparameter('Memory Window Length', memory.window_length)
logbook().record_hyperparameter('nb_steps_warmup', dqn.nb_steps_warmup)
logbook().record_hyperparameter('target_model_update', dqn.target_model_update)
logbook().record_hyperparameter('nb_actions', nb_actions)


# dqn.compile(Adam(lr=1e-3), metrics=['mae'])
dqn.compile(Adam(lr=1e-5), metrics=['mae'])

# Okay, now it's time to learn something! We visualize the training here for show, but this
# slows down training quite a lot. You can always safely abort the training prematurely using
# Ctrl + C.
# dqn.fit(env, nb_steps=50000, visualize=False, verbose=2)
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
logbook().submit()
