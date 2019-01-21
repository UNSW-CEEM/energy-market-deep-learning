# Electricity Market Deep Learning Framework.
The aim of this software is to provide an adversarial reinforcement learning model of a restructured electricity market, specifically Australia's National Electricity Market. It is intended to work as an environment plugin for Elon Musk's OpenAi gym. 


## Usage
Keras, Tensorflow and Python 3.* are required to run the simulations. 
The software consists of three components: The market simulation webserver, the keras machine reinforcement learning setup, and the user interface. These components communicate in real-time over websockets. 

## Demo
A video of the working UI and simulator can be found [here](https://youtu.be/-A0k6z4WAUY)
A demo, which works based on whether or not simulations are currently running, can be found [here](https://nem-control.herokuapp.com/)

![screenshot 1](https://user-images.githubusercontent.com/7201209/51462251-7917fa00-1da3-11e9-80c3-294284d20edb.png)

![screenshot 2](https://user-images.githubusercontent.com/7201209/51462319-a4024e00-1da3-11e9-95f4-abe95922cdc2.png)

## Notes on machine learning outcomes
Start with generators at >0 capacity - otherwise the many variables they have to optimise don't appear consistent with sending generation and price positive - it appears that by reducing generation at a negative price, score is improved.
Takes about 20,000 runs to get it to learn the market cap. Sometimes a few more

Atari games take ~18 million gens to learn - 30 fps. We do about 50 fps effective, with our sim. So OK speed with websockets.

Increasing fuzz (ie. epsilon) on the DDPG optimizer seems to instantly help - at least we follow a trend of the demand profile which is interesting.
I also increased default learning rate by a factor of 10 (0.001 to 0.01)

One problem is there is barely any discovery with the default settings. I increased sigma in the Ornstein-Uhlenbeck process which has made for a significantly more random appearance in the bidding - but I haven't yet had the model converge (not many runs though). 

Extremely good explanation: https://keon.io/deep-q-learning/


## References

At the moment, based on examples and code from Matthias Plappert, repo found here: https://github.com/matthiasplappert/keras-rl