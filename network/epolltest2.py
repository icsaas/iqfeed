import socket,select

for res in socket.getaddrinfo('0.0.0.0',1025,socket.AF_INET,socket.SOCK_STREAM):
    fa,socktype,proto,canonname,sa=res

SockServer=socket.socket(fa,socktype,proto)
SockServer.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
SockServer.bind(sa)
SockServer.listen(5)

epoll=select.epoll()
epoll.register(SocketServer.fileno(),select.EPOLLIN)

try:
    conns={}
    addrs={}
    while True:
        for fileno,event in epoll.poll(1):
            if fileno==SockServer.accept():
                conn,addr=SockServer.accept()

                epoll.register(conn.fileno(),select.EPOLLIN)
                conns[conn.fileno()]=conn
                addrs[conn.fileno()]=addr

                conn.send("----Welcome to server. Type EXIT to quit.---\n")
                print "[server]:accept connection from %s <%s>" % addr
            elif event&select.EPOLLIN:
                message=conns[fileno].recv(1024)
                print "%s<%s> say:"%(addrs[fileno][0])

                if b'EXIT' in message:
                    epoll.modify(fileno,select.EPOLLOUT)

                for key in conns.keys():
                    if key!=fileno:
                        conns[key].send("%s<%s> say:%s" %(addrs[key][0],addrs[key][1],message))
            elif event & select.EPOLLOUT:
                epoll.modify(fileno,0)
                conns[fileno].shutdown(socket.SHUT_RDWR)
            elif event & select.EPOLLHUP:
                epoll.unregister(fileno)
                conns[fileno].close()
                print '[server]: %s<%s> quit.' % addres[fileno]
                
                del conns[fileno]
                del addrs[fileno]
finally:
    epoll.unregister(SockServer.fileno())
    epoll.close()
    SockServer.close()
