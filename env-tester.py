import gym
import market_env
env = gym.make('MarketEnv-v0')
# env = gym.make('CartPole-v0')
env.reset()
for _ in range(1000):
	env.render()
	# print env.action_space.sample()
	# env.step(env.action_space.sample()) # take a random action