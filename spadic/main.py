import threading, Queue
from util import IndexQueue

import ftdi_cbmnet
from message import MessageSplitter, Message
from registerfile import SpadicRegisterFile
from shiftregister import SpadicShiftRegister
from control import SpadicController


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

    from util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text))

    def __init__(self, reset=False, load=None, **kwargs):
        try:
            self._cbmif = ftdi_cbmnet.FtdiCbmnet()
        except IOError:
            raise # TODO enter offline mode

        self._stop = self._cbmif._stop

        self.readout_enable(0)

        # message splitters and output queues for groups A and B
        self._dataA_splitter = MessageSplitter()
        self._dataB_splitter = MessageSplitter()
        self._dataA_queue = Queue.Queue()
        self._dataB_queue = Queue.Queue()

        # register read result Queue (indexable)
        self._ctrl_queue = IndexQueue()

        # data reader thread
        self._recv_worker = threading.Thread(name="recv worker")
        self._recv_worker.run = self._recv_job
        self._recv_worker.daemon = True
        self._recv_worker.start()

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

    def _recv_job(self):
        """Process data received from the CBMnet interface."""
        while not self._stop.is_set():
            try:
                (addr, words) = self._cbmif.read()
            except TypeError: # read result is None
                continue

            if addr == ftdi_cbmnet.ADDR_DATA_A:
                for m in self._dataA_splitter(words):
                    self._dataA_queue.put(m)

            elif addr == ftdi_cbmnet.ADDR_DATA_B:
                for m in self._dataB_splitter(words):
                    self._dataB_queue.put(m)

            elif addr == ftdi_cbmnet.ADDR_CTRL:
                [reg_addr, reg_val] = words
                self._ctrl_queue.put(reg_addr, reg_val)


    def __exit__(self, *args):
        """Bring all threads to halt."""
        if not hasattr(self, '_stop'):
            return
        if not self._stop.is_set():
            self._stop.set()
        self._cbmif.__exit__(*args)
        while self._recv_worker.is_alive():
            self._recv_worker.join(timeout=1)
        self._debug("[main]", self._recv_worker.name, "finished")

        
    #----------------------------------------------------------------
    # access register file
    #----------------------------------------------------------------
    def write_register(self, address, value):
        """Write a value into a register."""
        addr = ftdi_cbmnet.ADDR_CTRL
        words = [RF_WRITE, address, value]
        self._cbmif.write(addr, words)

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
            addr = ftdi_cbmnet.ADDR_CTRL
            words = [RF_READ, address, 0]
            self._cbmif.write(addr, words)
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
        addr = ftdi_cbmnet.ADDR_DLM
        words = [number]
        self._cbmif.write(addr, words)

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
        except Queue.Empty:
            return None
        return (data if raw else Message(data))

    def read_groupB(self, timeout=1, raw=False):
        """Get one message from group B, if available."""
        try:
            data = self._dataB_queue.get(timeout=timeout)
        except Queue.Empty:
            return None
        return (data if raw else Message(data))

