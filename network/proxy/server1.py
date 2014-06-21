from log import log
import socket
s=socket.socket()
s.bind(('0.0.0.0',31500))
s.listen(5)

while 1:
    cs,address=s.accept()
    log('got connected from'+str(address))
    cs.send('hello i am server,welcome')
    ra=cs.recv(512)
    log(ra)
    cs.close()

