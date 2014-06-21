import zmq

context=zmq.Context()
frontend=context.socket(zmq.XREP)
backend=context.socket(zmq.XREQ)
frontend.bind("tcp://0.0.0.0:39300")
backend.connect("tcp://127.0.0.1:9300")

poller=zmq.Poller()
poller.register(frontend,zmq.POLLIN)
poller.register(backend,zmq.POLLIN)

while True:
    socks=dict(poller.poll())

    if socks.get(frontend)==zmq.POLLIN:
        message=frontend.recv()
        more=frontend.getsockopt(zmq.RCVMORE)
        if more:
            backend.send(message,zmq.SNDMORE)
        else:
            backend.send(message)
    if socks.get(backend)==zmq.POLLIN:
        message=backend.recv()
        more=backend.getsockopt(zmq.RCVMORE)
        if more:
            frontend.send(message,zmq.SNDMORE)
        else:
            frontend.send(message)
