import soket,sys,os
def main():
    ls=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    port=int(sys.argv[1])
    ls.bind(('',port))

    while (1):
        ls.listen(1)
        (conn,addr)=ls.accept()
        print 'client is at ',addr
        #get w or ps command from client
        rc=conn.recv(2)
        #run the command in a Unix-style pipe
        ppn=os.popen(rc)#do ppn.close() to close
        #ppn is a "file-like object," so can apply readlines()
        rl=ppn.readlines()
        #create a file-like object from the connection socket
        flo=conn.makefile('w',0)
        #write the lines to the network
        flo.writelines(r1[:-1])
        #cleanup
        #must close both the socket and the wrapper
        flo.close()
        conn.close()

if __name__=="__main__":
    main()
