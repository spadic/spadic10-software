import json
import re
import socket
from main import Spadic

PORT_BASE = 45000
PORT_OFFSET = {"RF": 0, "SR": 1, "DATA": 2, "DLM": 3}

class SpadicBaseRequestServer:
    def __init__(self, port_base=None):
        port = (port_base or PORT_BASE) + self.port_offset
        # TODO optionally use AF_UNIX
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((socket.gethostname(), port))

        self.socket = s
        self.connection = None

    def start(self):
        self.socket.listen(1)
        print "waiting for connection on port", self.socket.getsockname()[1]
        c, a = self.socket.accept()
        try:
            name = socket.gethostbyaddr(a[0])[0]
        except:
            name = a[0]
        print "got connection from", name
        self.connection = c

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if self.connection:
            self.connection.close()
        self.socket.close()

    def run(self):
        if not self.connection:
            print "not connected."
            return
        buf = ''
        p = re.compile('\n')
        while True:
            received = self.connection.recv(64)
            if not received:
                print "lost connection"
                break
            data = buf + received
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
                self.process(decoded)


class SpadicRFServer(SpadicBaseRequestServer):
    port_offset = PORT_OFFSET["RF"]

    def __init__(self, registerfile, port_base=None):
        SpadicBaseRequestServer.__init__(self, port_base)
        self.registerfile = registerfile
            
    def process(self, decoded):
        command, registers = decoded
        if command == 'W':
            # registers must be a dictionary {name: value, ...}
            self.registerfile.write(registers)
        elif command == 'R':
            # registers must be a list [name1, name2, ...] or the string "all"
            contents = self.registerfile.read()
            if registers == "all":
                result = contents
            else:
                result = {name: contents[name] for name in registers}
            self.connection.sendall(json.dumps(result)+'\n')


class SpadicSRServer(SpadicBaseRequestServer):
    port_offset = PORT_OFFSET["SR"]

    def __init__(self, shiftregister, port_base=None):
        SpadicBaseRequestServer.__init__(self, port_base)
        self.shiftregister = shiftregister
            
    def process(self, decoded):
        command, registers = decoded
        if command == 'W':
            # registers must be a dictionary {name: value, ...}
            self.shiftregister.write(registers)
        elif command == 'R':
            # registers must be a list [name1, name2, ...] or the string "all"
            contents = self.shiftregister.read()
            if registers == "all":
                result = contents
            else:
                result = {name: contents[name] for name in registers}
            self.connection.sendall(json.dumps(result)+'\n')

