import json
import re
import socket
import struct
import threading
import time

from main import Spadic
from util import InfiniteSemaphore
import message


# inheritance tree:
# 
# BaseServer------------------------------
# \                                       \
#  BaseRequestServer-----                  BaseStreamServer
#  \                     \                 \
#   BaseRegisterServer    SpadicDLMServer   SpadicDataServer
#   \               \
#    SpadicRFServer  SpadicSRServer


PORT_BASE = 45000
PORT_OFFSET = {"RF": 0, "SR": 1, "DLM": 2, "DATA_A": 3, "DATA_B": 4}

WNOP = sum((v & m) for (v, m) in [message.preamble['wINF'],
                                  message.infotype['iNOP']])


class SpadicServer(Spadic):
    def __init__(self, reset=False, load=None, port_base=None, **kwargs):
        Spadic.__init__(self, reset, load, **kwargs)

        def _run_gen(cls, *args, **kwargs):
            with cls(*args, **kwargs) as serv:
                serv._stop = self._stop
                serv.run()

        try:
            debug = self._debug if kwargs['_debug_server'] else None
        except KeyError:
            debug = None

        def _run_rf_server():
            _run_gen(SpadicRFServer, self._registerfile, port_base, debug)

        def _run_sr_server():
            _run_gen(SpadicSRServer, self._shiftregister, port_base, debug)

        def _run_dlm_server():
            _run_gen(SpadicDLMServer, self.send_dlm, port_base, debug)

        def _run_dataA_server():
            _run_gen(SpadicDataServer, "A", self.read_groupA, port_base, debug)

        def _run_dataB_server():
            _run_gen(SpadicDataServer, "B", self.read_groupB, port_base, debug)

        self._rf_server = threading.Thread(name="RF server")
        self._rf_server.run = _run_rf_server
        self._rf_server.daemon = True
        self._rf_server.start()

        self._sr_server = threading.Thread(name="SR server")
        self._sr_server.run = _run_sr_server
        self._sr_server.daemon = True
        self._sr_server.start()

        self._dlm_server = threading.Thread(name="DLM server")
        self._dlm_server.run = _run_dlm_server
        self._dlm_server.daemon = True
        self._dlm_server.start()

        self._dataA_server = threading.Thread(name="DataA server")
        self._dataA_server.run = _run_dataA_server
        self._dataA_server.daemon = True
        self._dataA_server.start()

        self._dataB_server = threading.Thread(name="DataB server")
        self._dataB_server.run = _run_dataB_server
        self._dataB_server.daemon = True
        self._dataB_server.start()


    def __exit__(self, *args):
        Spadic.__exit__(self)
        if not self._stop.is_set():
            self._stop.set()
        for s in [self._rf_server, self._sr_server, self._dlm_server,
                  self._dataA_server, self._dataB_server]:
            s.join()


#---------------------------------------------------------------------------

class BaseServer:
    max_connections = None # default: infinity

    def __init__(self, port_base=None, _debug_func=None):
        self.port_base = port_base
        self.socket = None
        self.sem_conn = (
            InfiniteSemaphore() if self.max_connections is None
            else threading.BoundedSemaphore(self.max_connections))
        self._stop = None # needs to be overwritten by a threading.Event()
        if not _debug_func:
            def _debug_func(*args):
                pass
        self._debug = _debug_func

    def run(self):
        while not self._stop.is_set():
            if self.sem_conn.acquire(blocking=False):
                if self.socket is None:
                    self.socket = self.new_socket()
                    self.socket.listen(0)
                    self._debug("waiting for connection on port",
                                self.socket.getsockname()[1])
                try:
                    connection = self.wait_connection()
                except SystemExit:
                    return
                else:
                    t = threading.Thread()
                    def thread_serve():
                        self.serve(connection)
                    t.run = thread_serve
                    t.start()
            else: # max. connections reached
                if self.socket is not None:
                    # prevent further connection attempts
                    self.socket.close()
                self.socket = None
                time.sleep(1)

    def new_socket(self):
        """Create and return a new socket."""
        port = (self.port_base or PORT_BASE) + self.port_offset
        # TODO optionally use AF_UNIX
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(1)
        s.bind((socket.gethostname(), port))
        return s

    def wait_connection(self):
        """Wait for an incoming connection and return it."""
        while True:
            if self._stop.is_set():
                raise SystemExit
            try:
                c, a = self.socket.accept()
            except socket.timeout:
                continue
            else:
                break
        try:
            name = socket.gethostbyaddr(a[0])[0]
        except: # what could go wrong here??
            name = a[0]
        self._debug("got connection from", name)
        return c

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if not self._stop.is_set():
            self._stop.set()
        self.socket.close()
        self._debug("finished")

    def serve(self, connection):
        self._serve_job(connection)
        connection.close()
        self.sem_conn.release()

    def _serve_job(self, connection):
        raise NotImplementedError


#---------------------------------------------------------------------------

class BaseRequestServer(BaseServer):
    def _serve_job(self, connection):
        buf = ''
        p = re.compile('\n')
        while not self._stop.is_set():
            # TODO this cannot be aborted until data is received
            # if the connection was closed, '' is returned
            received = connection.recv(64)
            if not received:
                self._debug("lost connection")
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
                try:
                    response = self.process(decoded)
                    if response:
                        connection.sendall(response)
                    self._debug("processed", decoded)
                except:
                    self._debug("failed to process", decoded)
                    continue # don't crash on invalid input

    def process(self, decoded):
        raise NotImplementedError


#---------------------------------------------------------------------------

class SpadicDLMServer(BaseRequestServer):
    port_offset = PORT_OFFSET["DLM"]

    def __init__(self, dlm_send_func, port_base=None, debug=None):
        if debug:
            def _debug(*args):
                debug("[DLM server]", *args)
        else:
            _debug = None
        BaseRequestServer.__init__(self, port_base, _debug)
        self.send_dlm = dlm_send_func

    def process(self, decoded):
        self.send_dlm(decoded) # must be a number


#---------------------------------------------------------------------------

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
            try:
                if registers.lower() == "all":
                    result = contents
                else:
                    raise ValueError
            except AttributeError:
                result = {name: contents[name] for name in registers}
            return json.dumps(result)+'\n'

class SpadicRFServer(BaseRegisterServer):
    port_offset = PORT_OFFSET["RF"]

    def __init__(self, registerfile, port_base=None, debug=None):
        if debug:
            def _debug(*args):
                debug("[RF server]", *args)
        else:
            _debug = None
        BaseRegisterServer.__init__(self, port_base, _debug)
        self._registers = registerfile

class SpadicSRServer(BaseRegisterServer):
    port_offset = PORT_OFFSET["SR"]

    def __init__(self, shiftregister, port_base=None, debug=None):
        if debug:
            def _debug(*args):
                debug("[SR server]", *args)
        else:
            _debug = None
        BaseRegisterServer.__init__(self, port_base, _debug)
        self._registers = shiftregister


#---------------------------------------------------------------------------

# TODO use UDP/multicast?
class BaseStreamServer(BaseServer):
    max_connections = 1

    def _serve_job(self, connection):
        while not self._stop.is_set():
            data = self.read_data()
            encoded = self.encode_data(data)
            try:
                connection.sendall(encoded)
            except socket.error:
                self._debug("lost connection")
                break

    def read_data(self):
        raise NotImplementedError

    def encode_data(self, data):
        raise NotImplementedError


#---------------------------------------------------------------------------

class SpadicDataServer(BaseStreamServer):
    def __init__(self, group, data_read_func, port_base=None, debug=None):
        if not group in 'aAbB':
            raise ValueError
        g = group.upper()

        if debug:
            def _debug(*args):
                debug("[Data%s server]"%g, *args)
        else:
            _debug = None
        self.port_offset = PORT_OFFSET["DATA_%s"%g]
        BaseStreamServer.__init__(self, port_base, _debug)
        self._data_read_func = data_read_func

    def read_data(self):
        # try to read data - if it fails, we return a NOP word instead of
        # None, so that we can detect if the client has disconnected
        return self._data_read_func(timeout=1, raw=True) or [WNOP]

    def encode_data(self, data):
        # encode as unsigned short (16 bit), big-endian byte order
        return struct.pack('!'+str(len(data))+'H', *data)

