from gym.envs.registration import register

register(
    id='SimpleMarket-v0',
    entry_point='marketsim.openai.envs.simple:SimpleMarket',
)

register(
    id='MultiBidMarket-v0',
    entry_point='marketsim.openai.envs.multi_bid:MultiBidMarket',
)