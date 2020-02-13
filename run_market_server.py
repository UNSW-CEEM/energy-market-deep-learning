import socket    
import marketsim.io.servers.asyncserver as zmq_server

hostname = socket.gethostname()    
IPAddr = socket.gethostbyname(hostname)    
print("Your Computer Name is:" + hostname)    
print("Your Computer IP Address is:" + IPAddr) 
print("ZMQ Connection Point: tcp://"+IPAddr+":5570") 

zmq_server.main()