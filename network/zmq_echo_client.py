import zmq

c=zmq.Context()
s=c.socket(zmq.REQ)
s.connect("tcp://*:10001")
#s.connect('ipc://tmp/zmq')
s.send('hello')
msg=s.recv()
print msg