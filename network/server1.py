# -*- coding:utf-8 -*-
import socket
import asyncore
import threading

MAX_RECV=4096

#负责接收client的连线
class AgentServer(asyncore.dispatcher):
    def __init__(self,port):
        asyncore.dispatcher.__init__(self)
        self.clientSocket=None
        self.port=port
        #建立等待的socket
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.bind(('',self.port))
        self.listen(5)
    def handle_accept(self):
        self.clientSocket,address=self.accept()
        print 'New Client from: '+address[0]
        self.clientSocket=ClientAgent(self.clientSocket)

class ClientAgent(asyncore.dispatcher):
    def __init__(self,socket):
        asyncore.dispatcher.__init__(self,socket)
        self.SendData=""

    def handle_read(self):
        self.RecvData=self.recv(MAX_RECV)
        if len(self.RecvData) > 0:
            print "recv: "+self.RecvData
    def handle_write(self):
        send_byte=self.send(self.SendData)
        if send_byte > 0:
            send_out=self.SendData[:send_byte]
            self.SendData=self.SendData[send_byte:]
            self.handle_write()
        else:
            print "send all!!"
            self.SendData=""

    def writable(self):
        return False
    def handle_close(self):
        print "close connection : "+self.getpeername()[0]
        self.close()

class listen_client_thread(threading.Thread):
    def __init__(self,port):
        self.agentServer=AgentServer(port)
        threading.Thread.__init__(self)
    def run(self):
        print "Listen Client..."
        asyncore.loop()

class input_thread(threading.Thread):
    def __init__(self,listen_thread):
        self.listen_thread=listen_thread
        threading.Thread.__init__(self)
    def run(self):
        while 1:
            send_data=raw_input()
            self.listen_thread.agengServer.clientSocket.SendData=send_data
            self.listen_thread.agentServer.clientSocket.handle_write()

if __name__=="__main__":
    listen_thread=listen_client_thread(111)
    listen_thread.start()
    input_thread(listen_thread).start()



