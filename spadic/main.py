import threading, queue
from .util import IndexQueue

from . import ftdi_cbmnet
from .message import MessageSplitter, Message
from .registerfile import SpadicRegisterFile
from .shiftregister import SpadicShiftRegister
from .control import SpadicController


# CBMnet control port <-> register file read/write commands
RF_WRITE = 1
RF_READ  = 2


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

        self.readout_enable(0)

        self._dataA_splitter = MessageSplitter()
        self._dataB_splitter = MessageSplitter()
        self._dataA_queue = queue.Queue()
        self._dataB_queue = queue.Queue()
        self._ctrl_queue = IndexQueue()

        self._setup_threads()
        self._start_threads()

        # higher level register file access
        def rf_write_gen(name, addr):
            def write(value):
                self.write_register(addr, value)
            return write
        def rf_read_gen(name, addr):
            def read():
                return self.read_register(addr)
            return read
        self._registerfile = SpadicRegisterFile(rf_write_gen, rf_read_gen)

        # higher level shift register access
        self._shiftregister = SpadicShiftRegister(self.write_register,
                                                  self.read_register)

        # highest level configuration controller
        self.control = SpadicController(self._registerfile,
                                        self._shiftregister, reset, load)

        self.readout_enable(1)

    def __enter__(self):
        self._cbmif.__enter__()
        return self

    def __exit__(self, *args):
        self._stop_threads()
        self._cbmif.__exit__(*args)


    def _setup_threads(self):
        self._stop = threading.Event()

        self._dataA_worker = threading.Thread(name="dataA worker")
        self._dataA_worker.run = self._dataA_job
        self._dataA_worker.daemon = True

        self._dataB_worker = threading.Thread(name="dataB worker")
        self._dataB_worker.run = self._dataB_job
        self._dataB_worker.daemon = True

        self._ctrl_worker = threading.Thread(name="ctrl worker")
        self._ctrl_worker.run = self._ctrl_job
        self._ctrl_worker.daemon = True

    def _start_threads(self):
        self._dataA_worker.start()
        self._dataB_worker.start()
        self._ctrl_worker.start()

    def _stop_threads(self):
        if not hasattr(self, '_stop'):
            return
        if not self._stop.is_set():
            self._stop.set()
        for t in [self._dataA_worker, self._dataB_worker, self._ctrl_worker]:
            while t.is_alive():
                t.join(timeout=1)
            self._debug("[main]", t.name, "finished")


    def _dataA_job(self):
        """Process dataA received from the CBMnet interface."""
        while not self._stop.is_set():
            words = self._cbmif.read_data(lane=0)
            if not words:
                continue
            for m in self._dataA_splitter(words):
                self._dataA_queue.put(m)

    def _dataB_job(self):
        """Process dataB received from the CBMnet interface."""
        while not self._stop.is_set():
            words = self._cbmif.read_data(lane=1)
            if not words:
                continue
            for m in self._dataB_splitter(words):
                self._dataB_queue.put(m)

    def _ctrl_job(self):
        """Process control response received from the CBMnet interface."""
        while not self._stop.is_set():
            words = self._cbmif.read_ctrl()
            if not words:
                continue
            reg_addr, reg_val = words
            self._ctrl_queue.put(reg_addr, reg_val)


    #----------------------------------------------------------------
    # access register file
    #----------------------------------------------------------------
    def write_register(self, address, value):
        """Write a value into a register."""
        words = [RF_WRITE, address, value]
        self._cbmif.write_ctrl(words)

    def read_register(self, address, clear_skip=False,
                      request_skip=False, request_only=False):
        """Read the value from a register."""
        if not request_skip:
            if not clear_skip:
                # Workaround for retransmit bug in SPADIC 1.0 CBMnet:
                # Sometimes old register reads are retransmitted -> Clear
                # software read buffer before sending the read request to be
                # sure to get the newest value.
                self._ctrl_queue.clear(address)
                # End workaround
            words = [RF_READ, address, 0]
            self._cbmif.write_ctrl(words)
        if not request_only:
            try:
                return self._ctrl_queue.get(address, timeout=1)
            except IOError:
                raise
        

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
        try:
            data = self._dataA_queue.get(timeout=timeout)
        except queue.Empty:
            return None
        return (data if raw else Message(data))

    def read_groupB(self, timeout=1, raw=False):
        """Get one message from group B, if available."""
        try:
            data = self._dataB_queue.get(timeout=timeout)
        except queue.Empty:
            return None
        return (data if raw else Message(data))

