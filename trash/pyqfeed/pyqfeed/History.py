import datetime, threading, logging, time
import OldClient, dispatcher


class HistoryClient(dispatcher.Dispatcher):
    def stop(self):
        self.disconnect()

    def disconnect(self):
        logging.debug("Trying to disconnect...")
        self.client.stop()

    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 5009 # Default Level 1 port

    def __init__(self, (host, port) = (DEFAULT_HOST, DEFAULT_PORT)):
        dispatcher.Dispatcher.__init__(self)
        self.host = host
        self.port = port
        self.instrument = None
        self.exit_thread = threading.Event()

    def getHistory(self, instrument, date, num_days=1):
        self.exit_thread.clear()
        self.instrument = instrument

        self.client = OldClient.Client((self.host, self.port))
        self.client.set_listener('self', self)
        self.client.start()
        #self.client.send("HTD,%s,%i,,,,1" % (self.instrument, num_days))
        logging.debug("HDX,%s,%i,1<CR><LF>" % (self.instrument, num_days))
        #self.client.send("HID,%s,60,%i,,,,1" % (self.instrument, num_days))
        self.client.send("HDX,%s,%i,1<CR><LF>" % (self.instrument, num_days))
        self.client.join()
        time.sleep(1)
    def on_message(self,data):
        if data.startswith("E,!"):
            map(lambda l:l.on_error(data), self._listeners.values())
            self.disconnect()
        elif data.startswith("!ENDMSG!"):
            map(lambda l: l.on_data_end(),self._listeners.values())
            self.disconnect()
        else:
            map(lambda l: l.on_message(data),self._listeners.values())

