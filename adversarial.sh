python -m marketsim.io.servers.asyncserver > server.log &
python dqn_adversarial.py GEN_1 > nyngan.log & 
python dqn_adversarial.py GEN_2
# killall python