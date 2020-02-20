# Run this first, grab the IP address output, then run the next two commands
# floyd run --cpu python run_market_server.py
# echo "Follow link above, grab correct TCP IP address from console output, paste it in market_config as the MARKET_SERVER. You have 2 minutes."
# sleep 120

# GPU1
# floyd run --gpu --env tensorflow-1.3 python dqn_adversarial.py GEN_1
# floyd run --gpu --env tensorflow-1.3 python dqn_adversarial.py GEN_2

#GPU2
# floyd run --gpu2 --env tensorflow-1.4 python dqn_adversarial.py GEN_1
# floyd run --gpu2 --env tensorflow-1.4 python dqn_adversarial.py GEN_2

#CPU
floyd run --cpu --env tensorflow-1.4 python dqn_adversarial.py GEN_1
floyd run --cpu --env tensorflow-1.4 python dqn_adversarial.py GEN_2