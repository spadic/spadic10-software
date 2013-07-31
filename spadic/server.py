import json
import re
import socket
from main import Spadic

PORT_BASE = 45000
PORT_OFFSET = {"RF": 0, "SR": 1, "DATA": 2, "DLM": 3}

class SpadicServerRF:
    def __init__(self, port_base=None):
        port = (port_base or PORT_BASE) + PORT_OFFSET["RF"]
        # TODO optionally use AF_UNIX
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((socket.gethostname(), port))
        s.listen(1)
        print "waiting for connection"
        c, a = s.accept()
        try:
            name = socket.gethostbyaddr(a[0])[0]
        except:
            name = a[0]
        print "got connection from", name
        self.socket = s
        self.connection = c

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if self.connection:
            self.connection.close()
            print "closing", self.connection
        print "closing", self.socket
        self.socket.close()

    def run(self):
        buf = ''
        p = re.compile('\n')
        while True:
            data = buf + self.connection.recv(64)
            while True:
                    m = p.search(data)
                    if not m:
                            buf = data
                            break
                    i = m.end()
                    chunk, data = data[:i], data[i:]
                    try:
                        decoded = json.loads(chunk)
                    except ValueError:
                        continue
                    print decoded
            
