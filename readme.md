Electricity Market Deep Learning Framework.
At the moment, based on examples and code from Matthias Plappert, repo found here: https://github.com/matthiasplappert/keras-rl


##Notes on learning
-Start with generators at >0 capacity - otherwise the many variables they have to optimise don't appear consistent with sending generation and price positive - it appears that by reducing generation at a negative price, score is improved.
Takes about 20,000 runs to get it to learn the market cap. Sometimes a few more

Atari games take ~18 million gens to learn - 30 fps. We do about 50 fps effective, with our sim. So OK speed with websockets.

Increasing fuzz (ie. epsilon) on the DDPG optimizer seems to instantly help - at least we follow a trend of the demand profile which is interesting.
I also increased default learning rate by a factor of 10 (0.001 to 0.01)

One problem is there is barely any discovery with the default settings. I increased sigma in the Ornstein-Uhlenbeck process which has made for a significantly more random appearance in the bidding - but I haven't yet had the model converge (not many runs though). 

Extremely good explanation: https://keon.io/deep-q-learning/