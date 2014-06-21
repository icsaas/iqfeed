import asynchat
import socket
import logging

from cStringIO import StringIO
from dispatcher import  Dispatcher
import threading
import asyncore
import sys

class IQConnectSocketClient(asynchat.async_chat, Dispatcher):
    '''
    Low-level client to IQConnect socket interface

    In general, this class should not be instantiated directly. Instead, use one of the more specific service clients. e.g. :py:class:`pyqfeed.level1.Level1Client`
    '''
    DEFAULT_ADDR = ('127.0.0.1', 5009) #-----level1 data

    def __init__(self, sockaddr=DEFAULT_ADDR):
        asynchat.async_chat.__init__(self)
        Dispatcher.__init__(self)
        self._host, self._port = sockaddr
        self._receiver_thread = None
        self._receiver_thread_exiting = threading.Event()
        self._receiver_thread_exited = False
        self._ibuffer = ""
        # IQfeed separates rows with newline
        self.set_terminator("\r\n")


        #self.connect((self._host,self._port))


    def _connect_iqfeed(self):
        '''
        Initiate connection to IQFeed
        '''
        self.connected = False
        self.connecting = True
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self._host, self._port))
        self.set_socket(s)


    def connect(self):
        try:
            self._connect_iqfeed()
        except Exception, e:
            raise
        finally:
            pass

    def disconnect(self):
        try:
            self.close()
        except AttributeError:
            # Socket is already closed
            pass



       # logging.debug("handle read in asynchat")
       # if self.ac_in_buffer.startswith('!ENDMSG!'):
       #     return
#        else:
#            asynchat.async_chat.handle_read(self)


    def handle_error(self):
        '''
        Called when an unhandled exception occurs
        '''
        print 'this is a pity here'
        t, v, tb = sys.exc_info()
        logging.error(t)
        logging.error(v)

        self.close()

    def handle_connect(self):
        '''logging.error
        Called when connection is established
        '''
        self.connected = False
        logging.debug("Connected!")

        #self._q.put((None, None))

    def handle_close(self):
        logging.debug("Disconnected!")
        asynchat.async_chat.handle_close(self)
        self.disconnect()

    def collect_incoming_data(self, data):
        '''
        Buffer new data
        '''
        self._ibuffer+=data

    def found_terminator(self):
        '''
        Called when a new message has been received. See :py:class:`asynchat.async_chat`.
        '''
        self.new_message(self._ibuffer)
        if self.ac_in_buffer.startswith('!ENDMSG!'):
            self.stop()
        self._ibuffer=""

    def new_message(self,message):
        for listener in self._listeners.values():
            logging.debug("new messaging")
            listener.on_message(message)

    def send(self, message):
        '''
        Send message to IQConnect
        '''
        asynchat.async_chat.send(self, message )

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        #self._receiver_thread
        self.disconnect()

    def start(self):
        if self._receiver_thread:
            self.stop()
        self._receiver_thread_exiting.clear()
        self._connect_iqfeed()

        self._receiver_thread = threading.Thread(None, self._start_receive_loop)
        self._receiver_thread.start()
    def stop(self):
        logging.debug("Client.stop()")
        # Close the socket.
        try:
            self.close()
        except AttributeError:
            # Socket already closed.
            pass

        # Wait for the receiver thread to terminate.
        if self._receiver_thread != threading.currentThread():
            self._receiver_thread_exiting.wait()
    def join(self):
        if self._receiver_thread:
            logging.debug("Joining %s" % self._receiver_thread.getName())
            self._receiver_thread.join()

    def _start_receive_loop(self):
        threading.currentThread().setName("IQFeedReceive")
        logging.debug("Thread %s starting" % threading.currentThread().getName())
        try:
            #self._ibuffer = ""
            asyncore.loop()
        finally:
            logging.debug("Thread %s terminating..." % threading.currentThread().getName())
            self._receiver_thread_exiting.set()




