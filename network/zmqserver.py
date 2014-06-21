import zmq

context=zmq.Context()
socket=context.socket(zmq.REP)
socket.connect("tcp://*:5560")

while True:
    message=socket.recv()
    print "Received request: ",message
    socket.send("World")
