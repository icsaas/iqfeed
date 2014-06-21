import sys,socket,time,threading
loglock=threading,Lock()
def log(msg):
    loglock.acquire()
    try:
        print ' [%s]: \n%s\n' %(time.ctime(),msg.strip())
        sys.stdout.flush()
    finally:
        loglock.release()

class PipeThread(threading.Thread):
    def __init__(self,source,target):
        threading.Thread.__init__(self)
        self.source=source
        self.target=target


    def run(self):
        while Trur:
            try:
                data=self.source.recv(1024)
                log(data)
                if not data:
                    break
                self.target.send(data)
            except:
                break
            log('PipeThread done')

class Forwarding(threading.Thread):
    def __init__(self,port,targethost,targetport):
        number=random.randint(1,3)
        numbers='%d' %number
        portlist={'1':5009,'2':9100,'3':9200}
        host='127.0.0.1
        threading.Thread.__init__(self)
        self.targethost=targethost
        self.targetport=portlist[numbers]
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0',port))
        self.sock.listen(10)
    def run(self):
        while True:
            client_fd,client_addr=self.sock.accept()
            target_fd=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            target_fd.connect((self.targethost,portlist[numbers]))
            log('new connect')

            PipeThread(target_fd,client_fd).start()
            PipeThread(client_fd,target_fd).start()

if __name__=='__main__':
    print 'Starting'
    import sys
    import random
    number=random.randint(1,2)
    numbers='%d'%number
    portlist={'1':5009,'2':9100,'3':9200}
    host='127.0.0.1'
    Forwarding(9999,host,portlist[numbers]).start()