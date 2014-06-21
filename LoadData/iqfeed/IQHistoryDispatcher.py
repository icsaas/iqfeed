from dispatcher import Dispatcher
from async_handler import IQConnectSocketClient
import threading
import asyncore
import logging

class IQHistoryDispatcher(Dispatcher):
    DEFAULT_ADDR = ('172.20.143.221', 5009) #-----level1 data

    def __init__(self, sockaddr=DEFAULT_ADDR):
        Dispatcher.__init__(self)
        self._host, self._port = sockaddr
        #self._close_event = threading.Event()
        self._ibuffer = ""

    def getOptionChain(self,symbol):
        self.client = IQConnectSocketClient(sockaddr=(self._host, self._port))
        listener_name=symbol+'listen'
        self.client.set_listener('self',self)
        #send some message to get the history
        #self.client.connect()
        self.client.start()
        logging.debug("CEO,%s,pc,,4,,,,,OPTIONCHAIN\r\n" % symbol)
        self.client.send("CEO,%s,pc,,4,,,,,OPTIONCHAIN\r\n" % symbol)
        #self.client.disconnect()
        self.client.join()
        import time
        time.sleep(1)
        self.client.stop()
    def getHistory(self,option):
        self.client = IQConnectSocketClient(sockaddr=(self._host, self._port))
        listener_name=option+'listen'
        self.client.set_listener('self',self)
        #send some message to get the history
        #self.client.connect()
        self.client.start()
        #HDX,[symbol],[MaxDatapoints],[DataDirection--0/decrease 1/increase],[RequestID],[DatapointsPerSend]<CR><LF>
        logging.debug("HDX,%s,100,0,HDX\r\n" % "AAON1317H25")
        self.client.send("HDX,%s,100,0,HDX\r\n" % "AAON1317H25")
        #HIX,[Symbol],[Interval],[MaxDatapoints],[DataDirection],[RequestID],[DatapointsPerSend],[IntervalType]<CR><LF>
        #logging.debug("HIX,%s,60,100,0,HIX\r\n" % option)
        #self.client.send("HIX,%s,60,100,0,HIX\r\n" % option)
        #HTX,[Symbol],[MaxDatapoints],[DataDirection],[RequestID],[DatapointsPerSend]<CR><LF>
        #logging.debug("HTX,%s,100,0,HTX\r\n" % option)
        #self.client.send("HTX,%s,pc,,4,,,,,HTX\r\n" % "AAON1317H25")

        #self.client.disconnect()
        self.client.join()
        import time
        time.sleep(1)
        self.client.stop()
    def on_message(self,data):
        if "!ENDMSG!" in data:
            map(lambda l: l.on_data_end(), self._listeners.values())
            self.client.disconnect()
        elif "E," in data:
            map(lambda l: l.on_error(data), self._listeners.values())
            self.client.disconnect()
        else:
            map(lambda l: l.on_message(data), self._listeners.values())

        #if data.startswith("E,!"):
        #    map(lambda l: l.on_error(data), self._listeners.values())
        #    self.disconnect()
        #elif data.startswith("!ENDMSG!"):
        #    map(lambda l: l.on_data_end(), self._listeners.values())
        #    self.disconnect()
        #else:
        #    map(lambda l: l.on_message(data), self._listeners.values())
        #    #self.client.set_terminator('\n')



