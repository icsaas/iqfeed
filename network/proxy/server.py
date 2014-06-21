import socket
from log import *

address=('0.0.0.0',31500)
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind(address)
s.listen(5)

ss,addr=s.accept()
data='got connected from'+str(addr)
log(data)

ss.send('byebye')
ra=ss.recv(512)
log(ra)

ss.close()
s.close()