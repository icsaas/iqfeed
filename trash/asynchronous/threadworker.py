import time,datetime
import threading

def worker(a_tid,a_acount):
    global g_mutex
    print "Str ",a_tid,datetime.datetime.now()
    for i in range(1000000):
        g_mutex.acquire()
        a_acount.deposite(1)
        g_mutex.release()
    print "End ",a_tid,datetime.datetime.now()

class Account:
    def __init__(self,a_base):
        self.m_amount=a_base
    def deposite(self,a_amount):
        self.m_amount+=a_amount
    def withdraw(self,a_amount):
        self.m_amount-=a_amount

if __name__=="__main__":
    global g_mutex
    count=0
    dstart=datetime.datetime.now()
    print "Main Thread Start At:",dstart

    #init thread_pool
    thread_pool=[]
    #init mutex
    g_mutex=threading.Lock()
    #init thread items
    acc=Account(100)
    for i in range(10):
        th=threading.Thread(target=worker,args=(i,acc))
        thread_pool.append(th)
    #start threads one by one
    for i in range(10):
        thread_pool[i].start()

    #collect all threads
    for i in range(10):
        threading.Thread.join(thread_pool[i])
    dend=datetime.datetime.now()
    print "count=",acc.m_amount
    print "Main Thread End at:",dend,"time span",dend-dstart

import multiprocessing
import time

def func(msg):
    for i in xrange(3):
        print msg
        time.sleep(1)
    return "done"+msg

if __name__=="__main__":
    pool = multiprocessing.Pool(processes=4)
    result = []
    for i in xrange(10):
        msg="hello %d"%(i)
        result.append(pool.apply_async(func,(msg,)))
    pool.close()
    pool.join()
    for res in result:
        print res.get()
    print "Sub-process(es) done."
    

















