from .util import IndexQueue
import threading

class SpadicCbmnetRegisterAccess:
    """Read and write registers using the CBMnet control port."""

    WRITE = 1
    READ  = 2

    from .util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text))

    def __init__(self, cbmnet):
        self._cbmnet = cbmnet
        self._read_results = IndexQueue()
        self._setup_thread()

    def __enter__(self):
        self._start_thread()
        return self

    def __exit__(self, *args):
        self._stop_thread()

    def _setup_thread(self):
        self._stop = threading.Event()
        self._thread = threading.Thread(name='ctrl worker')
        self._thread.run = self._ctrl_job
        self._thread.daemon = True

    def _start_thread(self):
        self._thread.start()

    def _stop_thread(self):
        if not self._stop.is_set():
            self._stop.set()
        while self._thread.is_alive():
            self._thread.join(timeout=1)
        self._debug(self._thread.name, 'finished')

    def _ctrl_job(self):
        """Process control response received from the CBMnet interface."""
        while not self._stop.is_set():
            words = self._cbmnet.read_ctrl()
            if not words:
                continue
            reg_addr, reg_val = words
            self._read_results.put(reg_addr, reg_val)

    def write_register(self, address, value):
        """Write a value into a register."""
        words = [type(self).WRITE, address, value]
        self._cbmnet.write_ctrl(words)

    def read_register(self, address, clear_skip=False,
                      request_skip=False, request_only=False):
        """Read the value from a register."""
        if not request_skip:
            if not clear_skip:
                self._retransmit_workaround(address)
            words = [type(self).READ, address, 0]
            self._cbmnet.write_ctrl(words)
        if not request_only:
            return self._read_results.get(address, timeout=1)

    def _retransmit_workaround(self, address):
        """Workaround for the retransmit bug in SPADIC 1.0 CBMnet.

        Sometimes old register reads are retransmitted. Clear the read buffer
        before sending the read request to be sure to get the newest value.
        """
        self._read_results.clear(address)
