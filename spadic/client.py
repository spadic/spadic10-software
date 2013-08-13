import json
import re
import socket
import threading

from IndexQueue import IndexQueue
from server import PORT_BASE, PORT_OFFSET


class BaseRegisterClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        self._recv_queue = IndexQueue()
        self._recv_worker = threading.Thread(name="recv worker")
        self._recv_worker.run = self._recv_job
        self._recv_worker.daemon = True
        self._stop = threading.Event()

    def connect(self, server_address, port_base=None):
        port = (port_base or PORT_BASE) + self.port_offset
        self.socket.connect((server_address, port))
        self._recv_worker.start()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if not self._stop.is_set():
            self._stop.set()
        self.socket.close()

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
        """Process data received from the RF server."""
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

