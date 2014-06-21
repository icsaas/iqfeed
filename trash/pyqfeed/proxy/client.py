from log import log
import socket,threading,datetime,sys
loglock=threading.Lock()

def log(msg):
    loglock.acquire()
    try:
        print '[%s]: \n%s\n' % (datetime.datetime.now(),msg.strip())
        sys.stdout.flush()
    finally:
        loglock.release()

address=('127.0.0.1',31500)
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(address)

data=s.recv(512)
wrapdata='the data received is'+data
log(wrapdata)
s.send('hihi')
s.close()