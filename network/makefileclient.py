import socket,sys

def main():
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    host=sys.argv[1]
    port=int(sys.argv[2])
    s.connect((host,port))

    #send w or ps command to server
    s.send(sys.argv[3])

    #create "file-like object" flo
    flo=s.makefile('r',0)
    #now can call readlines() on flo,and also use the fact that
    #that stdout is a file-like object too
    sys.stdout.writelines(flo.readlines())
    if __name__=="__main__":
        main()

