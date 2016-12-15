import json
import re
import socket
import struct
import threading
import time
import queue

from .util import IndexQueue
from .control import SpadicController
from .control.ui import SpadicControlUI
from .message import _MessageSplitter, Message
from .registerfile import SpadicRegisterFile
from .server_ports import PORT_BASE, PORT_OFFSET
from .shiftregister import SPADIC_SR


# inheritance tree:
# 
# BaseClient-----------------
# \                          \
#  BaseReceiveClient-----     SpadicDLMClient
#  \                     \
#   BaseRegisterClient    SpadicDataClient
#   \               \
#    SpadicRFClient  SpadicSRClient


class BaseClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        self._stop = threading.Event()

    def connect(self, server_address, port_base=None):
        port = (port_base or PORT_BASE) + self.port_offset
        self.socket.connect((server_address, port))

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if not self._stop.is_set():
            self._stop.set()
        self.socket.close()

#--------------------------------------------------------------------

class BaseReceiveClient(BaseClient):
    def __init__(self):
        BaseClient.__init__(self)
        self._recv_worker = threading.Thread()
        self._recv_worker.run = self._recv_job
        self._recv_worker.daemon = True

    def connect(self, server_address, port_base=None):
        BaseClient.connect(self, server_address, port_base)
        self._recv_worker.start()

    def _recv_job(self):
        """Receive and process data from the server."""
        raise NotImplementedError

#--------------------------------------------------------------------

class BaseRegisterClient(BaseReceiveClient):
    def __init__(self, expires=2):
        BaseReceiveClient.__init__(self)
        self._recv_queue = IndexQueue()
        self._cache = {}
        self._expires = expires

    def _update_cache(self, register_values):
        self._cache.update({name: (value, time.time()+self._expires)
                            for (name, value) in register_values.items()})

    def write_registers(self, register_values):
        """
        Write registers.

        register_values must be a dictionary {name: value, ...}
        """
        self.socket.sendall(bytes(
            json.dumps(['w', register_values]) + '\n',
            'utf-8'))
        self._update_cache(register_values)

    def read_registers(self, registers):
        """
        Read registers.

        registers must be a sequence of register names.
        """
        needed = [name for name in registers
                  if (not name in self._cache or
                      time.time() > self._cache[name][1])]
        if needed:
            self.socket.sendall(bytes(
                json.dumps(['r', needed]) + '\n',
                'utf-8'))
            read = {name: self._recv_queue.get(name) for name in needed}
            self._update_cache(read)
        return {name: self._cache[name][0] for name in registers}

    def _recv_job(self):
        buf = b''
        p = re.compile(b'\n')
        while not self._stop.is_set():
            try:
                received = self.socket.recv(1024)
            except socket.timeout:
                continue
            data = buf + received
            while True:
                m = p.search(data)
                if not m:
                    buf = data
                    break
                i = m.end()
                chunk, data = data[:i], data[i:]
                try:
                    registers = json.loads(str(chunk, 'utf-8'))
                except ValueError:
                    continue
                for (name, value) in registers.items():
                    self._recv_queue.put(name, value)


class SpadicRFClient(BaseRegisterClient):
    port_offset = PORT_OFFSET["RF"]

class SpadicSRClient(BaseRegisterClient):
    port_offset = PORT_OFFSET["SR"]

#--------------------------------------------------------------------

class SpadicDLMClient(BaseClient):
    port_offset = PORT_OFFSET["DLM"]

    def send_dlm(self, value):
        self.socket.sendall(bytes(
            json.dumps(value) + '\n',
            'utf-8'))

#--------------------------------------------------------------------

class SpadicControlClient:
    """Client for the RF/SR/DLM parts of the SpadicServer."""

    def __init__(self, server_address, port_base=None,
                       reset=False, load=None, ui=False):
        self.rf_client = SpadicRFClient()
        self.sr_client = SpadicSRClient()
        self.dlm_client = SpadicDLMClient()

        # nested function generators!
        def gen_write_gen(client):
            def write_gen(name, addr):
                def write(value):
                    client.write_registers({name: value})
                return write
            return write_gen
        def gen_read_gen(client):
            def read_gen(name, addr):
                def read():
                    return client.read_registers([name])[name]
                return read
            return read_gen

        self.rf_client.connect(server_address, port_base)
        self.sr_client.connect(server_address, port_base)
        self.dlm_client.connect(server_address, port_base)

        # Create registerfile and shiftregister representations providing
        # the appropriate read and write methods.
        # The "use_cache" argument is set to False, because other clients can
        # modify the register configuration without our knowledge, so we
        # have to really read and write a register every time and cannot
        # rely on our last known values.
        self._registerfile = SpadicRegisterFile(
                                 gen_write_gen(self.rf_client),
                                 gen_read_gen(self.rf_client),
                                 use_cache=False)

        # The shiftregister actually behaves like the registerfile here,
        # we only have to override the default register map using SPADIC_SR.
        # format: {name: (address, size), ...}, (address not used here)
        sr_map = {name: (0, len(bits))
                  for (name, bits) in SPADIC_SR.items()}
        self._shiftregister = SpadicRegisterFile(
                                  gen_write_gen(self.sr_client),
                                  gen_read_gen(self.sr_client),
                                  register_map=sr_map,
                                  use_cache=False)

        # this is exactly like in main.Spadic
        self.control = SpadicController(self._registerfile,
                                        self._shiftregister, reset, load)
 
        # controller user interface
        self._ui = None
        if ui:
            self.ui_run()

    def ui_run(self):
        if not self._ui:
            self._ui = SpadicControlUI(self.control)
        self._ui.run()

    def send_dlm(self, value):
        self.dlm_client.send_dlm(value)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.rf_client.__exit__(*args, **kwargs)
        self.sr_client.__exit__(*args, **kwargs)
        self.dlm_client.__exit__(*args, **kwargs)

#--------------------------------------------------------------------

class SpadicDataClient(BaseReceiveClient):
    def __init__(self, group, server_address, port_base=None):
        BaseReceiveClient.__init__(self)
        self._recv_queue = queue.Queue()
        self._splitter = _MessageSplitter()

        if not group in 'aAbB':
            raise ValueError
        g = group.upper()
        self.port_offset = PORT_OFFSET["DATA_%s"%g]
        self.connect(server_address, port_base)

    def read_message(self, timeout=1, raw=False):
        try:
            data = self._recv_queue.get(timeout=timeout)
        except queue.Empty:
            return None
        return (data if raw else Message(data))

    def _recv_job(self):
        while not self._stop.is_set():
            try:
                received = self.socket.recv(1024)
            except socket.timeout:
                continue
            words = struct.unpack('!' + str(len(received) // 2) + 'H', received)
            for m in self._splitter(words):
                self._recv_queue.put(m)

