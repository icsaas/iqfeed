import socket
from log import log
s=socket.socket()

s.connect(('172.20.143.74',6542))
data=s.recv(512)
log('the data received is\n '+data)
s.send('hihi i am client')

sock2=socket.socket()
sock2.connect(('172.20.143.74',31500))
data2=sock2.recv(512)
log('the data received from server is\n '+data2)
sock2.send('client send use sock2')
sock2.close()
s.close()