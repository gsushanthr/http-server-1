from socket import *
import os
from threading import Thread 
from threading import *
mutex = Semaphore()
mutex2 = Semaphore()
print(mutex)
class ClientThread(Thread): 
 
    def __init__(self,conn,addr): 
        Thread.__init__(self) 
        self.conn = conn
        self.addr = addr 
    headers = {
        'Server': 'CrudeServer',
        'Content-Type': 'text/html',
    }

    status_codes = {
        200: 'OK',
        404: 'Not Found',
        501: 'Not Implemented',
        409: 'Resource already exists'
    }
    
    def handle_request(self,data):
        # Python's socket library receives and sends data as bytes, not as str (string). 
        # That's why we're using the b"" prefix with our strings. 
        # If we don't do that, we'll get an error.
        #   create an instance of `HTTPRequest`
       
        print("handling request")
        print(data)
        request = HTTPRequest(data)
       
        print(request.m)
        # now, look at the request method and call the 
        # appropriate handler
        
        try:
            handler = getattr(self, 'handle_%s' % request.m)
        except AttributeError:
            handler = self.HTTP_501_handler
        response = handler(request)
        return  response
    
    def response_line(self, status_code):
        """Returns response line"""
        reason = self.status_codes[status_code]
        line = "HTTP/1.1 %s %s\r\n" % (status_code, reason)

        return line.encode() # call encode to convert str to bytes

    def response_headers(self, extra_headers=None):
        """Returns headers
        The `extra_headers` can be a dict for sending 
        extra headers for the current response
        """
        headers_copy = self.headers.copy() # make a local copy of headers

        if extra_headers:
            headers_copy.update(extra_headers)

        headers = ""

        for h in headers_copy:
            headers += "%s: %s\r\n" % (h, headers_copy[h])

        return headers.encode() # call encode to convert str to bytes
    def HTTP_501_handler(self, request):
        response_line = self.response_line(status_code=501)

        response_headers = self.response_headers()

        blank_line = b"\r\n"

        response_body = b"<h1>501 Not Implemented</h1>"

        return b"".join([response_line, response_headers, blank_line, response_body])
    def handle_GET(self, request):
        global readcnt
        mutex2.acquire()
        readcnt = readcnt + 1
        if(readcnt==1):
            mutex.acquire()
        mutex2.release()
        print(request.uri)
        filename = request.uri.strip('/') # remove the slash from the request URI

        if os.path.exists(filename):
            response_line = self.response_line(status_code=200)

            response_headers = self.response_headers()

            with open(filename, 'rb') as f:
                response_body = f.read()
            print("data sent")
        else:
            response_line = self.response_line(status_code=404)
            response_headers = self.response_headers()
            response_body = b"<h1>404 Not Found</h1>"

        blank_line = b"\r\n"
        mutex2.acquire()
        readcnt = readcnt - 1
        if(readcnt==0):
            mutex.release()
        mutex2.release()
        return b"".join([response_line, response_headers, blank_line, response_body])

    def handle_POST(self,request):
        mutex.acquire()
        filename = request.uri.strip('/')
        print('/' + filename)
        just_filename = './' + os.path.basename(os.path.normpath(filename))
        if(os.path.exists(just_filename)):
            response_line = self.response_line(status_code = 409)
            response_headers = self.response_headers()
            response_body = b"<h1>Resource Already Exists</h1>"
            print("Resource already Exixts")
        else:    
            f = open('/' + filename,'r')
            f2 = open('./' + os.path.basename(os.path.normpath(filename)),'w+')
            data = f.read()
            f2.write(data)
            response_line = self.response_line(status_code=200)
            response_headers = self.response_headers()
            with open(just_filename, 'rb') as g:
                response_body = g.read()
            print("data got posted")
        blank_line = b"\r\n"
        mutex.release()
        # print(response_line + "\n", response_headers + "\n",blank_line,response_body + "\n")

        return b"".join([response_line, response_headers, blank_line,response_body])
    def handle_DELETE(self,request):
        mutex.acquire()
        filename = request.uri.strip('/')
        just_filename = './' + os.path.basename(os.path.normpath(filename))
        print(filename)
        if(os.path.exists(just_filename)):
            os.remove(just_filename)
            response_line = self.response_line(status_code=200)
            response_headers = self.response_headers()
            response_body = b"<h1>File Got deleted</h1>"  
            print("data got deleted")  
        else:
            response_line = self.response_line(status_code = 404)
            response_headers = self.response_headers()
            response_body = b"<h1>404 Not Found</h1>"
            print("data Not Found")
        blank_line = b"\r\n"
        mutex.release()
        return b"".join([response_line, response_headers, blank_line,response_body])
    def handle_PUT(self,request):
        mutex.acquire()
        new_filename = request.uri.strip('/')
        print(new_filename)
        just_filename = os.path.basename(os.path.normpath('/' + new_filename)) 
        print(just_filename)
        if(os.path.exists(just_filename)):
            os.remove(just_filename)
            f = open('/' + new_filename,'r')
            f2 = open(just_filename,'w+')
            data = f.read()
            f2.write(data)
            response_line = self.response_line(status_code = 200)
            response_headers = self.response_headers()
            with open(just_filename, 'rb') as g:
                response_body = g.read()
            print("data got updated")
            # return b"".join([response_line,response_headers,blank_line,response_body])
        else:
            response_line = self.response_line(status_code = 404)
            response_headers = self.response_headers()
            response_body = b"<h1>404 Not Found</h1>"
           
            print("Resource Not Found")
        blank_line = b"\r\n"
        mutex.release()
        return b''.join([response_line,response_headers,blank_line,response_body])  

    def run(self): 
        while True : 
            data = self.conn.recv(2048) 
            # print("Server received data:",data)
            response = self.handle_request(data)
            # send back the data to client
            self.conn.sendall(response)
            
class HTTPRequest():
    def __init__(self,data):
        self.m = "GET"
        self.uri = None
        self.http_version = "1.1" # default to HTTP/1.1 if request doesn't provide a version

        # call self.parse() method to parse the request data
        self.parse(data)
    def parse(self, data):
        lines = data.split(b"\r\n")

        request_line = lines[0]

        words = request_line.split(b" ")

        self.m = words[0].decode() # call decode to convert bytes to str
        if len(words) > 1:
            # we put this in an if-block because sometimes 
            # browsers don't send uri for homepage
            self.uri = words[1].decode() # call decode to convert bytes to str

        if len(words) > 2:
            self.http_version = words[2]
    
class TCPServer:
    def start(self,host,port):
        print("Tcpserver")
        self.host = host
        self.port = port
        # create a socket object
        s = socket(AF_INET, SOCK_STREAM)
        # bind the socket object to the address and port
        s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)           

        s.bind((self.host, self.port))
        # start listening for connections
        s.listen(5) #server can listen to 5 clients simultaneously
        # s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)           

        print("Listening at", s.getsockname())
        threads = []

        while(1):
            # accept any new connection
            (conn, addr) = s.accept()
            print("New server socket thread Connected from:" + str(addr))
            try:
                newthread = ClientThread(conn,addr)
                newthread.start()
                threads.append(newthread)
            except:
                print("Thread isn't created.")
            # read the data sent by the client
            # for the sake of this tutorial, 
            # we'll only read the first 1024 bytes
            # data = conn.recv(1024)
            # # print(data)
            # response = self.handle_request(data)
            # # send back the data to client
            # conn.sendall(response)

        # close the connection
        conn.close()
        s.close()

class HTTPServer(TCPServer):
   
    headers = {
        'Server': 'CrudeServer',
        'Content-Type': 'text/html',
    }

    status_codes = {
        200: 'OK',
        404: 'Not Found',
        501: 'Not Implemented',
        409: 'Resource Already Exists'
    }
    
if __name__ == '__main__':
    readcnt = 0
    host = 'localhost' # address for our server
    port = 8080 # port for our server
    server = HTTPServer()   
    server.start(host,port)
