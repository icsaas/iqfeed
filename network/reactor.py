import asyncore
import socket
class Server(asyncore.dispatcher):
    def __init__(self,host,port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host,port))
        self.h=[]
        self.listen(5)

    def handle_accepted(self,sock,addr):
        print ("Incoming connection from %s:%s" % sock.getpeername())
        self.h.append(Handler(sock))

class Handler(asyncore.dispatcher):
    def __init__(self,sock):
        asyncore.dispatcher__init__(self,sock)
        self.writebuffer=b""

    def handle_read(self):
        data=self.recv(8192)
        if data:
            print ("[client]: %s" % data)
            self.writebuffer=b"Message received"

    def handle_close(self):
        print ("Client has left the building")
        self.close()

    def handle_write(self):
        if self.writebuffer:
            self.send(self.writebuffer)
            self.writebuffer=b""

server=Server("0.0.0.0",8080)
asyncore.loop()