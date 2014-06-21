import asyncore,socket,asynchat

class SimpleProxy(asyncore.dispatcher):
    def __init__(self,ip,port,listen_port=8080):
        self.ip=ip
        self.port=port
        self.listen_port=listen_port
        self.listen_address='0.0.0.0'
        asyncore.dispatcher.__init__(self)

        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((self.listen_address,self.listen_port))
        self.listen(128)

    def handle_accept(self):
        channel,address=self.accept()
        RequestChannel(channel,self.ip,self.port,self)

class RequestChannel(asynchat.async_chat):
    def __init__(self,channel,ip,port,server):
        self.server=server
        self.response=ResponseChannel(self,ip,port)
        asynchat.async_chat.__init__(self,channel)
        self.set_terminator(None)
    def handle_close(self):
        self.close()
        self.response.close()
    def handle_expt(self):
        self.close()
        self.response.close()
    def collect_incoming_data(self,data):
        self.send_data(data)

    def send_data(self,data):
        self.response.push(data)
    def found_terminator(self):
        pass


class ResponseChannel(asynchat.async_chat):
    def __init__(self,request,ip,port):
        self.request=request
        asynchat.async_chat.__init__(self)
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connect((ip,port))
        self.set_terminator(None)

    def handle_close(self):
        self.close()
        self.request.close()

    def handle_expt(self):
        self.close()
        self.request.close()
    def send_data(self,data):
        self.request.push(data)
    def collect_incoming_data(self,data):
        self.send_data(data)

    def found_terminator(self):
        pass

SimpleProxy('localhost',8080,8083)
asyncore.loop()


















