import socket
import select
import Queue

server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.setblocking(False)
server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
server_address=("localhost",10001)

print "Starting up on %s port %s" % server_address
server.bind(server_address)
server.listen(5)
message_queues={}
#The timeout value is represente in milliseconds,instead of seconds
timeout=100
#Create a limit for the next
READ_ONLY=(select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR)
READ_WRITE=(READ_ONLY|select.POLLOUT)

#set up the poller
poller=select.poll()
poller.register(server,READ_ONLY)
#map file descriptors to socket objects
fd_to_socket={server.fileno():server,}
while True:
    print "Waiting for the next event"
    events=poller.poll(timeout)
    print "*"*20
    print len(events)
    print events
    print "*"*20
    for fd,flag in events:
        s=fd_to_socket[fd]
        if flag & (select.POLLIN|select.POLLPRI):
            if s is server:
                #A readable socket is ready to accept a connection
                connection,client_address=s.accept()
                print "Connection ",client_address
                connection.setblocking(False)

                fd_to_socket[connection.fileno()]=connection
                poller.register(connection,READ_ONLY)

                #Give the connection a queue to send data
                message_queues[connection]=Queue.Queue
            else:
                data=s.recv(1024)
                if data:
                    # A readable client socket has data
                    print " received %s from %s " % (data,s.getpeername())
                    message_queues[s].put(data)
                    poller.modify(s,READ_WRITE)
                else:
                    #Close the connection
                    print " closing ",s.getpeername()
                    #Stop listening for input on the connection
                    poller.unregister(s)
                    s.close()
                    del message_queues[s]
        elif flag & select.POLLHUP:
            #A client that "Hang up",to be closed.
            print "closing ",s.getpeername,"(HUP)"
            poller.unregister(s)
            s.close()
        elif flag & select.POLLOUT:
            #SOCKET is ready to send DATA,if there is any to send
            try:
                next_msg=message_queues[s].get_nowait()
            except Queue.Empty:
                #No messages waiting so stop checking
                print s.getpeername," queue empty"
                poller.modify(s,READ_ONLY)
            else:
                print " sending %s to %s" %(next_msg,s.getpeername())
                s.send(next_msg)
        elif flag & select.POLLERR:
            #Any events with POLLER cause the server to close the sockets
            print " exception on",s.getpeername()
            poller.unregister(s)
            s.close()
            del message_queues[s]

