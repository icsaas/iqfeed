import zmq

c=zmq.Context()
s=c.socket(zmq.REP)
s.bind("tcp://*:10001")
#s.bind('ipc://tmp/zmq')

while True:
    msg=s.recv()
    s.send(msg)
s.close()