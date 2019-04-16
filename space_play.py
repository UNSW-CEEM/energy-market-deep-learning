import gym
import marketsim.openai.envs
import space_wrappers
# An environment with a continuous action space.
# We first turn it into a MultiDiscrete, and then into
# a flat discrete action space.
env = gym.make('MultiBidMarket-v0')
# wrapped = space_wrappers.DiscretizedActionWrapper(env, 3)
wrapped = space_wrappers.FlattenedActionWrapper(env)

# this is now a single integer
print(wrapped.action_space.n)