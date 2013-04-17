import ftdi_cbmnet
import threading, Queue
import time


# CBMnet control port <-> register file read/write commands
RF_WRITE = 1
RF_READ  = 2


class Spadic(ftdi_cbmnet.FtdiCbmnet):
    """Wrapper for CBMnet interface <-> SPADIC communication."""

    def __init__(self):
        ftdi_cbmnet.FtdiCbmnet.__init__(self)

        # set up Queues
        self._write_queue = Queue.Queue()
        self._read_queue = Queue.Queue()

        # set up Threads
        self._cbmif_thread = threading.Thread()
        self._cbmif_thread.run = self._cbmif_task
        self._cbmif_thread.daemon = True
        self._cbmif_thread.start()


    def _cbmif_task(self):
        """Process write tasks and read all available data."""
        while True:
            while not self._write_queue.empty():
                (addr, words) = self._write_queue.get()
                self._cbmif_write(addr, words)
                self._write_queue.task_done()

            try:
                (addr, words) = self._cbmif_read()
                self._read_queue.put((addr, words))
            except TypeError: # read result is None
                if self._write_queue.empty():
                    time.sleep(0.1)
                    # otherwise the main thread becomes unresponsive
                continue
        
    #----------------------------------------------------------------
    # register file access
    #----------------------------------------------------------------
    def write_register(self, address, value):
        """Write a value into a single register."""
        addr = ftdi_cbmnet.ADDR_CTRL
        words = [RF_WRITE, address, value]
        self._write_queue.put((addr, words))

    def read_register(self, address):
        """Read the value from a single register."""
        addr = ftdi_cbmnet.ADDR_CTRL
        words = [RF_READ, address, 0]
        self._write_queue.put((addr, words))
        # TODO actually return the register value
        
    #----------------------------------------------------------------
    # DLM control
    #----------------------------------------------------------------
    def send_dlm(self, number):
        """Send a DLM."""
        addr = ftdi_cbmnet.ADDR_DLM
        words = [number]
        self._write_queue.put((addr, words))

