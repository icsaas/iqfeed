
class TCPListenerThread(StoppableThread):
    def __init__(selfself,tcp_port):
        StoppableThread.__init__(self)
        self.tcp_port=tcp_port
        self.sock=socket.socket(socket.AF_INET,
                                socket.SOCK_STREAM)
        self.sock.bind((LOCAL_ADDRESS,self.tcp_port))
        self.sock.listen()
    def runCallback(self):
        print "Listen on "+str(self.tcp_port)+".."
        conn,addr=self.sock.accept()

        if isFromDTN(addr):
            tcpProxy=getProxyFromPort(tcp_port)
            if not tcpProxy:
                tcpProxy=TCPProxy(host,true)
        else:
            host=addr[0]
            tcpProxy=getProxyFromHost(host)
            if not tcpProxy:
                tcpProxy=TCPProxy(host,False)

        tcpProxy.handle(conn)
    def finalCallback(selfself):
        self.sock.close()

class TCPProxy():
    def __init__(self,remote,isFromDTN):
        #remote = port for Server or Remote host for Client
        self.isFromDTN=isFromDTN
        self.conn=None

        #If listening from a node
        if not isFromDTN:
            #set node remote host
            self.remoteHost=remote
            TcpProxyHostRegister[self.remoteHost]=self

            #set port to DTN interface + listener
            self.portToDTN=getNewTCPPort()
            TCPPortToHost[self.portToDTN]=self.remoteHost
            newTCPListenerThread(self.portToDTN)
        #or from DTN
        else:
            self.portToDTN=remote
            TCPProxyPortRegister[self.portToDTN]=self
            self.remoteHost=getRemoteFromPortTCP(self.portToDTN)

    def handle(self,conn):
        print 'New Connection!'

        #shouldn't happen,but eh
        if self.conn != None:
            self.closeConnections()

        self.conn=conn

        #init socket with remote
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        if self.isFromDTN:
            self.sock.connect((self.remoteHost,4556))#TODO:handle dynamic port...
        else:
            self.sock.connect((DTN_Address,DTN_TCPPort))

        self.handlerThread=newTCPHandlerThread(self)
        self.replyThread=newTCPReply(self)
    def closeConnections(self):
        try:
            if self.conn != None:
                print 'Close connections!'
                self.sock.close()
                self.conn.close()
                self.conn=None
                self.handlerThread.kill()
                self.replyThread.kill()
        except Exception,err:
            print str(err)

    def forward(self,data):
        print "TCP forwarding data: "+data
        self.conn.send(data)

    def forwardBack(self,data):
        print "TCP forwarding data back: "+data
        self.conn.send(data)

class TCPHandlerThread(StoppableThread):
    def __init__(self,proxy):
        StoppableThread.__init__(self)
        self.proxy=proxy
    def runCallback(self):
        test=False
        while 1:
            data=self.proxy.conn.recv(BUFFER_SIZE)
            if test:
                self.proxy.sock.close()
            test = True
            if not data:
                break
            print "TCP received data: ",data
            self.proxy.forward(data)
        self.kill()
    def finalCallback(self):
        self.proxy.closeConnections()

class TCPReplyThread(StoppableThread):
    def __init__(self,proxy):
        StoppableThread.__init__(self)
        self.proxy=proxy

    def runCallback(self):
        while 1:
            data=self.proxy.sock.recv(BUFFER_SIZE)
            if not data:
                break
            print "TCP received back data: "+data
            self.proxy.forwardBack(data)
        self.kill()
    def finalCallback(self):
        self.proxy.closeConnections()



