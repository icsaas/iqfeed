import socket,traceback,os,sys,select

class stateclass:

    stdmask=select.POLLERR|select.POLLHUP|select.POLLNVAL

    def __init__(self,mastersock):
        self.p=select.poll()
        self.mastersock=mastersock
        self.watchread(mastersock)