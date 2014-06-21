import sys
import asyncore
import asynchat
import socket
import logging
import random
import select

import web

from LoadData.iqfeed.dispatcher import Dispatcher
import Listener

from IQListener import IQListener
from IQHistoryDispatcher import IQHistoryDispatcher

import StringIO



import os, csv
def loadSymbolsFromFile(filename):
    base, ext = os.path.splitext(filename)
    symbols = []

    if ext.lower() == ".csv":
        for row in csv.reader(open(filename, "rb")):
            symbols.append(row[0])
    return symbols

def GetOptionChain(symbols):
    c1 = IQHistoryDispatcher(sockaddr=proxy_sockaddr)
    for symbol in symbols:
        listener = IQListener(instrument=symbol, date_split=True,type='OPTIONCHAIN')
        c1.set_listener('optchianlistener',listener)
        c1.getOptionChain(symbol)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    proxy_sockaddr = ('localhost', 9100)
    symbols = loadSymbolsFromFile('symbols.csv')
    #for symbol in symbols:
    #option loading
    #GetOptionChain(symbols)
    #getOption history
    import web
    from Model.setting import  *
    db = web.database(dbn='mysql', host=mysqlhost, port=mysqlport, user=mysqlusername, pw=mysqlpassword, db=iqfeeddatabase)
    c1 = IQHistoryDispatcher(sockaddr=proxy_sockaddr)
    for symbol in symbols:
        tablename=symbol+'option'
        options=db.select(tablename,what='optionname')
        for option in options:
            option=str(option.optionname)
            hislistener=IQListener(instrument=option,date_split=True,type='HISTORY')
            c1.set_listener("historylistener",hislistener)
            c1.getHistory(option)














        
