import threading
from .util import IndexQueue

from . import ftdi_cbmnet
from .message import MessageSplitter
from .registerfile import SpadicRegisterFile
from .shiftregister import SpadicShiftRegister
from .control import SpadicController


class SpadicCbmnetRegisterAccess:
    """Read and write registers using the CBMnet control port."""

    WRITE = 1
    READ  = 2

    from .util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text))

    def __init__(self, cbmnet):
        self._cbmnet = cbmnet
        self._ctrl_queue = IndexQueue()
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
            self._ctrl_queue.put(reg_addr, reg_val)

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
            return self._ctrl_queue.get(address, timeout=1)

    def _retransmit_workaround(self, address):
        """Workaround for the retransmit bug in SPADIC 1.0 CBMnet.

        Sometimes old register reads are retransmitted. Clear the read buffer
        before sending the read request to be sure to get the newest value.
        """
        self._ctrl_queue.clear(address)


class Spadic:
    """
    Wrapper for CBMnet interface <-> SPADIC communication.
    
    Arguments:
    reset - flag for initial reset of the chip configuration
    load  - name of .spc configuration file to be loaded
    """

    from .util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text))

    def __init__(self, reset=False, load=None, **kwargs):
        self._cbmif = ftdi_cbmnet.FtdiCbmnet()
        self._reg_access = SpadicCbmnetRegisterAccess(self._cbmif)
        self._splitters = [MessageSplitter(self._cbmif, lane)
                           for lane in [0, 1]]

        self.readout_enable(0)

        # higher level register file access
        def rf_write_gen(name, addr):
            def write(value):
                self._reg_access.write_register(addr, value)
            return write
        def rf_read_gen(name, addr):
            def read():
                return self._reg_access.read_register(addr)
            return read
        self._registerfile = SpadicRegisterFile(rf_write_gen, rf_read_gen)

        # higher level shift register access
        self._shiftregister = SpadicShiftRegister(
            self._reg_access.write_register, self._reg_access.read_register)

        # highest level configuration controller
        self.control = SpadicController(self._registerfile,
                                        self._shiftregister, reset, load)

        self.readout_enable(1)

    def __enter__(self):
        self._cbmif.__enter__()
        self._reg_access.__enter__()
        for s in self._splitters:
            s.__enter__()
        return self

    def __exit__(self, *args):
        for s in self._splitters:
            s.__exit__()
        self._reg_access.__exit__()
        self._cbmif.__exit__(*args)

    #----------------------------------------------------------------
    # send DLMs
    #----------------------------------------------------------------
    def send_dlm(self, number):
        """Send a DLM."""
        words = [number]
        self._cbmif.write_command(words)

    def readout_enable(self, enable):
        """Start or stop data taking in the chip."""
        dlm = 8 if enable else 9
        self.send_dlm(dlm)
        

    #----------------------------------------------------------------
    # read messages from groups A and B
    #----------------------------------------------------------------
    def read_groupA(self, timeout=1, raw=False):
        """Get one message from group A, if available."""
        return self._splitters[0].read_message(timeout, raw)

    def read_groupB(self, timeout=1, raw=False):
        """Get one message from group B, if available."""
        return self._splitters[1].read_message(timeout, raw)
