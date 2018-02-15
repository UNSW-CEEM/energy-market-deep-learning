import numpy as np
import gym
import market_env
# from market_env.market_env import ElectricityMarket, Single_Ownership_Market_Interface
from ml_interfaces import Single_Ownership_Participant_Interface

import keras

from rl.agents.dqn import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory
import tensorflow as tf
from keras import backend as K
import time


from keras.models import Sequential, Model
from keras.layers import Dense, Activation, Flatten, Input, merge
from keras.optimizers import Adam

from rl.agents import DDPGAgent
from rl.memory import SequentialMemory
from rl.random import OrnsteinUhlenbeckProcess

import threading

import sys

tf_session = K.get_session()
tf_graph = tf.get_default_graph()
def train_generator(generator_label, gens, lrmc, capacity_MW):
    

    # Build an interface for the agent to access the shared environment
    env = Single_Ownership_Participant_Interface(generator_label, gens, lrmc, capacity_MW)
    nb_actions = env.action_space.shape[0]

    actor = Sequential()
    actor.add(Flatten(input_shape=(1,) + env.observation_space.shape))
    actor.add(Dense(16))
    actor.add(Activation('relu'))
    actor.add(Dense(16))
    actor.add(Activation('relu'))
    actor.add(Dense(16))
    actor.add(Activation('relu'))
    actor.add(Dense(nb_actions))
    actor.add(Activation('linear'))
    print(actor.summary())

    action_input = Input(shape=(nb_actions,), name='action_input')
    observation_input = Input(shape=(1,) + env.observation_space.shape, name='observation_input')
    flattened_observation = Flatten()(observation_input)
    # x = keras.layers.concatenate([action_input, flattened_observation]) #NEW
    x = merge([action_input, flattened_observation], mode='concat') #OLD
    x = Dense(32)(x)
    x = Activation('relu')(x)
    x = Dense(32)(x)
    x = Activation('relu')(x)
    x = Dense(32)(x)
    x = Activation('relu')(x)
    x = Dense(1)(x)
    x = Activation('linear')(x)
    critic = Model(inputs=[action_input, observation_input], outputs=x)
    print(critic.summary())

    # Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
    # even the metrics!
    memory = SequentialMemory(limit=100000, window_length=1)
    random_process = OrnsteinUhlenbeckProcess(size=nb_actions, theta=.15, mu=0., sigma=.3)
    agent = DDPGAgent(nb_actions=nb_actions, actor=actor, critic=critic, critic_action_input=action_input,
                    memory=memory, nb_steps_warmup_critic=100, nb_steps_warmup_actor=100,
                    random_process=random_process, gamma=.99, target_model_update=1e-3)
    agent.compile(Adam(lr=.001, clipnorm=1.), metrics=['mae'])

    # Okay, now it's time to learn something! We visualize the training here for show, but this
    # slows down training quite a lot. You can always safely abort the training prematurely using
    # Ctrl + C.
    agent.fit(env, nb_steps=50000, visualize=True, verbose=2, nb_max_episode_steps=200)
    return agent





ENV_NAME = 'MarketEnv-v0'


# Get the environment and extract the number of actions.
# env = gym.make(ENV_NAME)

# env = ElectricityMarket()

def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts


# Usage python main.py -label <generator_label>
if __name__ == '__main__':
    myargs = getopts(sys.argv)
    label = myargs['-label']

    gens = {
        'Bayswater':{
            'type':'coal',
            'capacity_MW':3000,
            'lrmc':30,
        },
        'Eraring':{
            'type':'coal',
            'capacity_MW':1000,
            'lrmc':70
        },
        # 'Liddell',
        # 'Mt Piper',
        # 'Vales Point B' ,
        # 'Colongra',
        # 'Liddell',
        # 'Tallawarra',
        # 'Smithfield',
        # 'Uraniquity',
    }

    train_generator(label, gens, gens[label]['lrmc'], gens[label]['capacity_MW'])
    # At the start, multiple access to same model from different thread produces error, so we wait a little while
    # Hacky but solution found here https://github.com/fchollet/keras/issues/5223
    # time.sleep(5)

# for g in gens:
#     # Build an interface for the agent to access the shared environment
#     agent_environment = Single_Ownership_Market_Interface(env, g)

#     actor = Sequential()
#     actor.add(Flatten(input_shape=(1,) + env.observation_space.shape))
#     actor.add(Dense(16))
#     actor.add(Activation('relu'))
#     actor.add(Dense(16))
#     actor.add(Activation('relu'))
#     actor.add(Dense(16))
#     actor.add(Activation('relu'))
#     actor.add(Dense(nb_actions))
#     actor.add(Activation('linear'))
#     print(actor.summary())

#     action_input = Input(shape=(nb_actions,), name='action_input')
#     observation_input = Input(shape=(1,) + env.observation_space.shape, name='observation_input')
#     flattened_observation = Flatten()(observation_input)
#     x = merge([action_input, flattened_observation], mode='concat')
#     x = Dense(32)(x)
#     x = Activation('relu')(x)
#     x = Dense(32)(x)
#     x = Activation('relu')(x)
#     x = Dense(32)(x)
#     x = Activation('relu')(x)
#     x = Dense(1)(x)
#     x = Activation('linear')(x)
#     critic = Model(input=[action_input, observation_input], output=x)
#     print(critic.summary())

#     # Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
#     # even the metrics!
#     memory = SequentialMemory(limit=100000, window_length=1)
#     random_process = OrnsteinUhlenbeckProcess(size=nb_actions, theta=.15, mu=0., sigma=.3)
#     agent = DDPGAgent(nb_actions=nb_actions, actor=actor, critic=critic, critic_action_input=action_input,
#                     memory=memory, nb_steps_warmup_critic=100, nb_steps_warmup_actor=100,
#                     random_process=random_process, gamma=.99, target_model_update=1e-3)
#     agent.compile(Adam(lr=.001, clipnorm=1.), metrics=['mae'])

#     # Okay, now it's time to learn something! We visualize the training here for show, but this
#     # slows down training quite a lot. You can always safely abort the training prematurely using
#     # Ctrl + C.
#     agent.fit(agent_environment, nb_steps=50000, visualize=True, verbose=2, nb_max_episode_steps=200)
#     # threading.Thread(target=agent.fit, args=(agent_environment,), kwargs={'nb_steps':50000, 'visualize':True, 'verbose':2, 'nb_max_episode_steps': 200} ).start()

# After training is done, we save the final weights.
# agent.save_weights('ddpg_{}_weights.h5f'.format(ENV_NAME), overwrite=True)

# # Finally, evaluate our algorithm for 5 episodes.
# agent.test(env, nb_episodes=5, visualize=True, nb_max_episode_steps=200)





