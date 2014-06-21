from rq import Queue, Worker, Connection
from trash.rq.worker import conn

if __name__ == '__main__':
    # Tell rq what Redis connection to use
    with Connection():
        q = Queue(connection=conn)
        Worker(q).work()
