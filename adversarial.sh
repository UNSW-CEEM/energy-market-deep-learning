python -m marketsim.io.servers.asyncserver > server.log &
python dqn_adversarial.py Nyngan > nyngan.log & 
python dqn_adversarial.py Bayswater
# killall python