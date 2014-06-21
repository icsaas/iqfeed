import asyncore
import logging
import socket

from echoserver import EchoServer
from asyncclient import EchoClient

logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s:%(message)s',
                    )
address=('localhost',0)
server=EchoServer(address)
ip,port=server.address

message_data=open('lorem.txt','r').read()*2

client=EchoClient(ip,port,message=message_data)

asyncore.loop()