import json
import re
import socket
import struct
import threading
import Queue

from IndexQueue import IndexQueue
from control import SpadicController
from control.ui import SpadicControlUI
from message import MessageSplitter, Message
from registerfile import SpadicRegisterFile
from server import PORT_BASE, PORT_OFFSET
from shiftregister import SPADIC_SR

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
    def __init__(self):
        BaseReceiveClient.__init__(self)
        self._recv_queue = IndexQueue()

    def write_registers(self, register_values):
        """
        Write registers.

        register_values must be a dictionary {name: value, ...}
        """
        self.socket.sendall(json.dumps(['w', register_values])+'\n')

    def read_registers(self, registers):
        """
        Read registers.

        registers must be a sequence of register names.
        """
        self.socket.sendall(json.dumps(['r', registers])+'\n')
        return {name: self._recv_queue.get(name) for name in registers}

    def _recv_job(self):
        buf = ''
        p = re.compile('\n')
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
                    registers = json.loads(chunk)
                except ValueError:
                    continue
                for (name, value) in registers.iteritems():
                    self._recv_queue.put(name, value)


class SpadicRFClient(BaseRegisterClient):
    port_offset = PORT_OFFSET["RF"]

class SpadicSRClient(BaseRegisterClient):
    port_offset = PORT_OFFSET["SR"]

#--------------------------------------------------------------------

class SpadicDLMClient(BaseClient):
    port_offset = PORT_OFFSET["DLM"]

    def send_dlm(self, value):
        self.socket.sendall(json.dumps(value)+'\n')

#--------------------------------------------------------------------

class SpadicControlClient:
    """Client for the RF/SR parts of the SpadicServer."""

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
        self._registerfile = SpadicRegisterFile(
                                 gen_write_gen(self.rf_client),
                                 gen_read_gen(self.rf_client))

        # The shiftregister actually behaves like the registerfile here,
        # we only have to override the default register map using SPADIC_SR.
        # format: {name: (address, size), ...}, (address not used here)
        sr_map = {name: (0, len(bits))
                  for (name, bits) in SPADIC_SR.iteritems()}
        self._shiftregister = SpadicRegisterFile(
                                  gen_write_gen(self.sr_client),
                                  gen_read_gen(self.sr_client),
                                  register_map=sr_map)

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
        self._recv_queue = Queue.Queue()
        self._splitter = MessageSplitter()

        if not group in 'aAbB':
            raise ValueError
        g = group.upper()
        self.port_offset = PORT_OFFSET["DATA_%s"%g]
        self.connect(server_address, port_base)

    def read_message(self, timeout=1, raw=False):
        try:
            data = self._recv_queue.get(timeout=timeout)
        except Queue.Empty:
            return None
        return (data if raw else Message(data))

    def _recv_job(self):
        while not self._stop.is_set():
            try:
                received = self.socket.recv(1024)
            except socket.timeout:
                continue
            words = struct.unpack('!'+str(len(received)/2)+'H', received)
            for m in self._splitter(words):
                self._recv_queue.put(m)

