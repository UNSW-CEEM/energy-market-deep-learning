from gym.envs.registration import register

register(
    id='MarketEnv-v0',
    entry_point='market_env.market_env:ElectricityMarket',
    max_episode_steps=200,
    reward_threshold=195.0,
)