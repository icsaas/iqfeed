import sys,os
from socket import *

from tool.logger import initlog
logger=initlog(__name__)

if sys.platform.startswith('win'):
    logger.debug("Launching IQConnect.")
    os.system(r'iqconnect.exe -product IQFEED_DEMO -version 1.0')
    logger.debug("Verifying if IQConnect is connected to the server.")
    bConnected=False
    #connect to the admin port.
    message=['helloworld network world']
    serverHost='localhost'
    serverPort=9300
    sock=socket(AF_INET,SOCK_STREAM)
    sock.connect((serverHost,serverPort))

    for line in message:
        data=sock.recv(1024)
        print 'client received:',repr(data)


    #loop while we are still connected to the admin port or until we are connected



    #cleanup admin port connection



    #at this point,we are connected and the feed is ready.

    #sting to hold what the user typed in.



