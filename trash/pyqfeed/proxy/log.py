import threading,datetime,sys
loglock=threading.Lock()

def log(msg):
    loglock.acquire()
    try:
        print '[%s]: \n%s\n' % (datetime.datetime.now(),msg.strip())
        sys.stdout.flush()
    finally:
        loglock.release()