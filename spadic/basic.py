import ftdi_cbmnet
import threading, Queue


# CBMnet control port <-> register file read/write commands
RF_WRITE = 1
RF_READ  = 2


class Spadic(ftdi_cbmnet.FtdiCbmnet):
    """Wrapper for CBMnet interface <-> SPADIC communication."""

    def __init__(self):
        ftdi_cbmnet.FtdiCbmnet.__init__(self)

        self._dataA_queue = Queue.Queue()
        self._dataB_queue = Queue.Queue()

        # register read buffer
        self._rf_read_buffer = {}
        self._rf_read_done = threading.Event()

        # Threads
        self._data_proc_thread = threading.Thread()
        self._data_proc_thread.run = self._data_proc_task
        self._data_proc_thread.daemon = True
        self._data_proc_thread.start()


    def _data_proc_task(self):
        """Process all read data."""
        while True:
            (addr, words) = self._cbmif_read()

            if addr == ftdi_cbmnet.ADDR_DATA_A:
                self._dataA_queue.put(words)

            elif addr == ftdi_cbmnet.ADDR_DATA_B:
                self._dataB_queue.put(words)

            elif addr == ftdi_cbmnet.ADDR_CTRL:
                [reg_addr, reg_val] = words
                self._rf_read_buffer[reg_addr] = reg_val
                self._rf_read_done.set()

        
    #----------------------------------------------------------------
    # register file access
    #----------------------------------------------------------------
    def write_register(self, address, value):
        """Write a value into a single register."""
        addr = ftdi_cbmnet.ADDR_CTRL
        words = [RF_WRITE, address, value]
        self._cbmif_write(addr, words)


    def read_register(self, address):
        """Read the value from a single register."""
        addr = ftdi_cbmnet.ADDR_CTRL
        words = [RF_READ, address, 0]

        self._rf_read_done.clear()
        self._cbmif_write(addr, words)
        self._rf_read_done.wait()
        return self._rf_read_buffer[address]
        
    #----------------------------------------------------------------
    # DLM control
    #----------------------------------------------------------------
    def send_dlm(self, number):
        """Send a DLM."""
        addr = ftdi_cbmnet.ADDR_DLM
        words = [number]
        self._cbmif_write(addr, words)

