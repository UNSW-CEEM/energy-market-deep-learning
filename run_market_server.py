import socket    
import marketsim.io.servers.asyncserver as zmq_server
import urllib.request

# hostname = socket.gethostname()    
# IPAddr = socket.gethostbyname(hostname)    
# print("Your Computer Name is:" + hostname)    
# print("Your Computer IP Address is:" + IPAddr) 



external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')

print("External IP",external_ip)
print("ZMQ Connection Point: tcp://"+external_ip+":5570") 

zmq_server.main()