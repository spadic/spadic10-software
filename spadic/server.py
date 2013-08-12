import json
import re
import socket
import struct
import threading
from main import Spadic

PORT_BASE = 45000
PORT_OFFSET = {"RF": 0, "SR": 1, "DLM": 2, "DATA_A": 3, "DATA_B": 4}


class SpadicServer(Spadic):
    def __init__(self, reset=False, load=None, port_base=None, **kwargs):
        Spadic.__init__(self, reset, load, **kwargs)

        def _run_gen(cls, *args, **kwargs):
            with cls(*args, **kwargs) as serv:
                serv._stop = self._stop
                while not serv._stop.is_set():
                    try:
                        serv.wait_connection()
                    except SystemExit:
                        return
                    serv.run()

        debug = self._debug if '_debug_server' in kwargs else None

        def _run_rf_server():
            _run_gen(SpadicRFServer, self._registerfile, debug=debug)

        def _run_sr_server():
            _run_gen(SpadicSRServer, self._shiftregister, debug=debug)

        def _run_dlm_server():
            _run_gen(SpadicDLMServer, self.send_dlm, debug=debug)

        def _run_dataA_server():
            def data_read_func():
                return self.read_groupA(raw=True)
            _run_gen(SpadicDataServer, "A", data_read_func, debug=debug)

        def _run_dataB_server():
            def data_read_func():
                return self.read_groupB(raw=True)
            _run_gen(SpadicDataServer, "B", data_read_func, debug=debug)

        self._rf_server = threading.Thread(name="RF server")
        self._rf_server.run = _run_rf_server
        self._rf_server.start()

        self._sr_server = threading.Thread(name="SR server")
        self._sr_server.run = _run_sr_server
        self._sr_server.start()

        self._dlm_server = threading.Thread(name="DLM server")
        self._dlm_server.run = _run_dlm_server
        self._dlm_server.start()

        self._dataA_server = threading.Thread(name="DataA server")
        self._dataA_server.run = _run_dataA_server
        self._dataA_server.start()

        self._dataB_server = threading.Thread(name="DataB server")
        self._dataB_server.run = _run_dataB_server
        self._dataB_server.start()


    def __exit__(self, *args):
        Spadic.__exit__(self)
        if not hasattr(self, '_stop'):
            return
        if not self._stop.is_set():
            self._stop.set()
        for s in [self._rf_server, self._sr_server, self._dlm_server]:
            s.join()
            self._debug("[main]", s.name, "finished")


#---------------------------------------------------------------------------
# BaseServer

class BaseServer:
    def __init__(self, port_base=None, _debug_func=None):
        port = (port_base or PORT_BASE) + self.port_offset
        # TODO optionally use AF_UNIX
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(1)
        s.bind((socket.gethostname(), port))

        self.socket = s
        self.connection = None
        self._stop = None # can be replaced by a threading.Event() object
        if not _debug_func:
            def _debug_func(*args):
                pass
        self._debug = _debug_func

    def wait_connection(self):
        self.socket.listen(1)
        self._debug("waiting for connection on port",
                    self.socket.getsockname()[1])
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
        self._debug("got connection from", name)
        self.connection = c

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if self.connection:
            self.connection.close()
        self.socket.close()


#---------------------------------------------------------------------------
# BaseServer
# \
#  BaseRequestServer

class BaseRequestServer(BaseServer):
    def run(self):
        if not self.connection:
            self._debug("not connected.")
            return
        buf = ''
        p = re.compile('\n')
        while self._stop is None or not self._stop.is_set():
            # TODO this cannot be aborted until data is received
            received = self.connection.recv(64)
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
                    self.process(decoded)
                    self._debug("processed", decoded)
                except:
                    self._debug("failed to process", decoded)
                    continue # don't crash on invalid input


#---------------------------------------------------------------------------
# BaseServer
# \
#  BaseRequestServer
#  \
#   SpadicDLMServer

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
# BaseServer
# \
#  BaseRequestServer
#  \
#   BaseRegisterServer
#   \               \
#    SpadicRFServer  SpadicSRServer

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
            self.connection.sendall(json.dumps(result)+'\n')

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
# BaseServer
# \
#  BaseStreamServer

class BaseStreamServer(BaseServer):
    def run(self):
        if not self.connection:
            self._debug("not connected.")
            return
        while self._stop is None or not self._stop.is_set():
            data = self.read_data()
            if data is not None:
                encoded = self.encode_data(data)
                try:
                    self.connection.sendall(encoded)
                except socket.error:
                    self._debug("lost connection")
                    break

    def read_data(self):
        raise NotImplementedError

    def encode_data(self, data):
        raise NotImplementedError


#---------------------------------------------------------------------------
# BaseServer
# \
#  BaseStreamServer
#  \
#   SpadicDataServer

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
        self.read_data = data_read_func

    def encode_data(self, data):
        # encode as unsigned short (16 bit), big-endian byte order
        return struct.pack('!'+str(len(data))+'H', *data)

