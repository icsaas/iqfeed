import asynchat_echo_server
interface='127.0.0.1'
port=1717
server=asynchat_echo_server.EchoServer((interface,port))
server.serve_forever()