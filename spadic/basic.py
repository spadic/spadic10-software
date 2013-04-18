import threading, Queue
import ftdi_cbmnet
from message import MessageSplitter, Message


# CBMnet control port <-> register file read/write commands
RF_WRITE = 1
RF_READ  = 2


class Spadic(ftdi_cbmnet.FtdiCbmnet):
    """Wrapper for CBMnet interface <-> SPADIC communication."""

    def __init__(self):
        ftdi_cbmnet.FtdiCbmnet.__init__(self)

        # message splitters for groups A and B
        self._dataA_splitter = MessageSplitter()
        self._dataB_splitter = MessageSplitter()

        # message output Queues and register read Queue
        self._dataA_queue = Queue.Queue()
        self._dataB_queue = Queue.Queue()
        self._ctrl_queue = Queue.Queue()

        # data reader thread
        self._cbmif_read_thread = threading.Thread()
        self._cbmif_read_thread.run = self._cbmif_read_task
        self._cbmif_read_thread.daemon = True
        self._cbmif_read_thread.start()


    def _cbmif_read_task(self):
        """Read and process data from the CBMnet interface."""
        while True:
            (addr, words) = self._cbmif_read()

            if addr == ftdi_cbmnet.ADDR_DATA_A:
                for m in self._dataA_splitter(words):
                    self._dataA_queue.put(m)

            elif addr == ftdi_cbmnet.ADDR_DATA_B:
                for m in self._dataB_splitter(words):
                    self._dataB_queue.put(m)

            elif addr == ftdi_cbmnet.ADDR_CTRL:
                [reg_addr, reg_val] = words
                self._ctrl_queue.put((reg_addr, reg_val))

        
    #----------------------------------------------------------------
    # access register file
    #----------------------------------------------------------------
    def write_register(self, address, value):
        """Write a value into a register."""
        addr = ftdi_cbmnet.ADDR_CTRL
        words = [RF_WRITE, address, value]
        self._cbmif_write(addr, words)


    def read_register(self, address):
        """Read the value from a register."""
        addr = ftdi_cbmnet.ADDR_CTRL
        words = [RF_READ, address, 0]

        self._cbmif_write(addr, words)
        (reg_addr, reg_val) = self._ctrl_queue.get()
        if reg_addr == address:
            return reg_val
        

    #----------------------------------------------------------------
    # send DLMs
    #----------------------------------------------------------------
    def send_dlm(self, number):
        """Send a DLM."""
        addr = ftdi_cbmnet.ADDR_DLM
        words = [number]
        self._cbmif_write(addr, words)
        

    #----------------------------------------------------------------
    # read messages from groups A and B
    #----------------------------------------------------------------
    def read_groupA(self):
        """Get one message from group A, if available."""
        if not self._dataA_queue.empty():
            return Message(self._dataA_queue.get())
        else:
            return None

    def read_groupB(self):
        """Get one message from group B, if available."""
        if not self._dataB_queue.empty():
            return Message(self._dataB_queue.get())
        else:
            return None

