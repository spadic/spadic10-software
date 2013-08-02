import json
import re
import socket
import threading
from main import Spadic

PORT_BASE = 45000
PORT_OFFSET = {"RF": 0, "SR": 1, "DATA": 2, "DLM": 3}


#---------------------------------------------------------------------------
# BaseRequestServer

class BaseRequestServer:
    def __init__(self, port_base=None):
        port = (port_base or PORT_BASE) + self.port_offset
        # TODO optionally use AF_UNIX
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(1)
        s.bind((socket.gethostname(), port))

        self.socket = s
        self.connection = None
        self._stop = None # can be replaced by a threading.Event() object

    def wait_connection(self):
        self.socket.listen(1)
        print "waiting for connection on port", self.socket.getsockname()[1]
        while True:
            if not(self._stop is None or not self._stop.is_set()):
                raise SystemExit
            try:
                c, a = self.socket.accept()
                break
            except socket.timeout:
                continue
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
        while self._stop is None or not self._stop.is_set():
            print "waiting for data"
            # TODO this cannot be aborted until data is received
            received = self.connection.recv(64)
            print "received", received
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
                print "processing", decoded
                try:
                    self.process(decoded)
                except:
                    continue # don't crash on invalid input


#---------------------------------------------------------------------------
# BaseRequestServer
#  \
#  SpadicDLMServer

class SpadicDLMServer(BaseRequestServer):
    port_offset = PORT_OFFSET["DLM"]

    def __init__(self, dlm_send_func, port_base=None):
        BaseRequestServer.__init__(self, port_base)
        self.send_dlm = dlm_send_func

    def process(self, decoded):
        self.send_dlm(decoded) # must be a number


#---------------------------------------------------------------------------
# BaseRequestServer
#  \
#  BaseRegisterServer
#   \               \
#   SpadicRFServer  SpadicSRServer

class BaseRegisterServer(BaseRequestServer):
    # needs an attribute self._registers,
    # e.g. SpadicShiftRegister or SpadicRegisterFile

    def process(self, decoded):
        command, registers = decoded
        if command.lower() == 'w':
            # registers must be a dictionary {name: value, ...}
            self._registers.write(registers)
        elif command.lower() == 'r':
            # registers must be a list [name1, name2, ...] or the string "all"
            contents = self._registers.read()
            if registers.lower() == "all":
                result = contents
            else:
                result = {name: contents[name] for name in registers}
            self.connection.sendall(json.dumps(result)+'\n')

class SpadicRFServer(BaseRegisterServer):
    port_offset = PORT_OFFSET["RF"]

    def __init__(self, registerfile, port_base=None):
        BaseRegisterServer.__init__(self, port_base)
        self._registers = registerfile

class SpadicSRServer(BaseRegisterServer):
    port_offset = PORT_OFFSET["SR"]

    def __init__(self, shiftregister, port_base=None):
        BaseRegisterServer.__init__(self, port_base)
        self._registers = shiftregister

