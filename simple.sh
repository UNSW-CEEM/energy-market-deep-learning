python -m marketsim.io.servers.asyncserver > server.log &
python -m marketsim.io.clients.asyncclient > client.log &
python dqn_simplemarket.py
# killall python