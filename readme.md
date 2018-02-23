Electricity Market Deep Learning Framework.
At the moment, based on examples and code from Matthias Plappert, repo found here: https://github.com/matthiasplappert/keras-rl


##Notes on learning
-Start with generators at >0 capacity - otherwise the many variables they have to optimise don't appear consistent with sending generation and price positive - it appears that by reducing generation at a negative price, score is improved.
Takes about 20,000 runs to get it to learn the market cap. Sometimes a few more

Atari games take ~18 million gens to learn - 30 fps. We do about 50 fps effective, with our sim. So OK speed with websockets.