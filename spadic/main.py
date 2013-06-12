import threading, Queue
from IndexQueue import IndexQueue

import ftdi_cbmnet
from message import MessageSplitter, Message
from registerfile import SpadicRegisterFile
from shiftregister import SpadicShiftRegister
from control import SpadicController


# CBMnet control port <-> register file read/write commands
RF_WRITE = 1
RF_READ  = 2


class Spadic(ftdi_cbmnet.FtdiCbmnetThreaded):
    """Wrapper for CBMnet interface <-> SPADIC communication."""

    def __init__(self, reset=0, ui=0, **kwargs):
        ftdi_cbmnet.FtdiCbmnetThreaded.__init__(self)
        self.__dict__.update(kwargs)

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
        self._registerfile = SpadicRegisterFile(self)

        # higher level shift register access
        self._shiftregister = SpadicShiftRegister(self)

        # highest level configuration controller
        self.control = SpadicController(self, reset, ui)

        self.readout_enable(1)


    def _recv_job(self):
        """Process data received from the CBMnet interface."""
        while not self._stop.is_set():
            try:
                (addr, words) = self._cbmif_read()
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
        if not self._stop.is_set():
            self._stop.set()
        ftdi_cbmnet.FtdiCbmnetThreaded.__exit__(self)
        self._recv_worker.join()
        if self._debug_cbmif:
            self._debug(self._recv_worker.name, "finished")

        
    #----------------------------------------------------------------
    # access register file
    #----------------------------------------------------------------
    def write_register(self, address, value):
        """Write a value into a register."""
        addr = ftdi_cbmnet.ADDR_CTRL
        words = [RF_WRITE, address, value]
        self._cbmif_write(addr, words)

    def read_register(self, address,
                      request_skip=False, request_only=False):
        """Read the value from a register."""
        if not request_skip:
            addr = ftdi_cbmnet.ADDR_CTRL
            words = [RF_READ, address, 0]
            self._cbmif_write(addr, words)
        if not request_only:
            try:
                return self._ctrl_queue.get(address, timeout=10)
            except IOError:
                raise

    def _test_read_register(self):
        try:
            self.read_register(8)
            success = True
        except IOError:
            success = False
        return success
        

    #----------------------------------------------------------------
    # send DLMs
    #----------------------------------------------------------------
    def send_dlm(self, number):
        """Send a DLM."""
        addr = ftdi_cbmnet.ADDR_DLM
        words = [number]
        self._cbmif_write(addr, words)

    def readout_enable(self, enable):
        """Start or stop data taking in the chip."""
        dlm = 8 if enable else 9
        self.send_dlm(dlm)
        

    #----------------------------------------------------------------
    # read messages from groups A and B
    #----------------------------------------------------------------
    def read_groupA(self, timeout=1):
        """Get one message from group A, if available."""
        try:
            return Message(self._dataA_queue.get(timeout=timeout))
        except Queue.Empty:
            return None

    def read_groupB(self, timeout=1):
        """Get one message from group B, if available."""
        try:
            return Message(self._dataB_queue.get(timeout=timeout))
        except Queue.Empty:
            return None

