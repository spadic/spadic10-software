import Ftdi
import threading, Queue
import time


# CBMnet port addresses
ADDR_DLM    = 0
ADDR_CTRL   = 1
ADDR_DATA_A = 2
ADDR_DATA_B = 3

# writable CBMnet ports and appropriate number of words
WRITE_LEN = {
  ADDR_DLM : 1,
  ADDR_CTRL: 3
}


class FtdiCbmnet(Ftdi.Ftdi):
    """Wrapper for FTDI <-> CBMnet interface communication."""

    def _cbmif_write(self, addr, words):
        """Access CBMnet send interface through FTDI write port.
        
        addr: Address of the CBMnet send port
        words: List of 16-bit words to be sent

        This method builds a data packet for the CBMnet send interface and
        transfers the individual bytes in the correct order through the
        FTDI write port.
        """
        if addr not in WRITE_LEN:
            raise ValueError("Cannot write to this CBMnet port.")
        if len(words) != WRITE_LEN[addr]:
            raise ValueError("Wrong number of words for this CBMnet port.")

        header = [addr, len(words)]
        data = []
        for w in words:
            high, low = w//0x100, w%0x100
            data.append(high)
            data.append(low)
        ftdi_data = header + data

        return self._ftdi_write(ftdi_data)//2

    def _cbmif_read(self):
        """Access CBMnet receive interface through FTDI read port.

        This method tries to read data from the FTDI and reconstruct a
        packet from the CBMnet receive interface.

        If successful, it returns a tuple (addr, words):
        addr: Address of the CBMnet receive port
        words: List of received 16-bit words

        Otherwise, it does not block, but return None instead.
        """
        header = self._ftdi_read(2, max_iter=1)
        if len(header) < 2:
            return None
        
        [addr, num_words] = header
        data = self._ftdi_read(2*num_words)
        words = []
        for i in range(num_words):
            high, low = data[2*i], data[2*i+1]
            w = (high<<8) + low
            words.append(w)

        return (addr, words)



class FtdiCbmnetThreaded(FtdiCbmnet):
    """FTDI <-> CBMnet interface communication with threads."""

    def __init__(self):
        FtdiCbmnet.__init__(self)

        # set up write/read threads
        self._write_queue = Queue.Queue()
        self._write_thread = threading.Thread()
        self._write_thread.run = self._cbmif_write_run
        self._write_thread.daemon = True

        self._read_queue = Queue.Queue()
        self._read_thread = threading.Thread()
        self._read_thread.run = self._cbmif_read_run
        self._read_thread.daemon = True

        self._manager_queue = Queue.Queue()
        self._manager_thread = threading.Thread()
        self._manager_thread.run = self._cbmif_manager_run
        self._manager_thread.daemon = True

        # start threads
        self._write_thread.start()
        self._read_thread.start()
        self._manager_thread.start()


    #--------------------------------------------------------------------
    # support "with" statement -> __exit__ is guaranteed to be called
    #--------------------------------------------------------------------
    def __exit__(self, *args):
        self._write_queue.join()
        self._manager_queue.join()
        self._read_queue.join()
        FtdiCbmnet.__exit__(self, args)


    #--------------------------------------------------------------------
    # these methods provide the user interface
    #--------------------------------------------------------------------
    def _cbmif_write(self, addr, words):
        """Write words to the CBMnet send interface."""
        self._write_queue.put((addr, words))

    def _cbmif_read(self):
        """Read words from the CBMnet receive interface."""
        result = self._read_queue.get()
        self._read_queue.task_done()
        return result


    #--------------------------------------------------------------------
    # these methods are run in separate threads and connect the user
    # interface to the lower level write/read operations
    #
    # the read operation is triggered by three sources:
    # - after each write operation
    # - after each successful read operation
    # - periodically every 10 seconds
    #--------------------------------------------------------------------
    def _cbmif_write_run(self):
        """Take write tasks and pass them to the manager."""
        while True:
            write_task = self._write_queue.get()
            self._manager_queue.put(write_task)
            self._manager_queue.put(None)
            self._write_queue.task_done()

    def _cbmif_read_run(self):
        """Periodically tell the manager to read."""
        while True:
            self._manager_queue.put(None)
            time.sleep(10)
                
    def _cbmif_manager_run(self):
        """Take write/read tasks from the queue and process them."""
        while True:
            task = self._manager_queue.get()
            if task is None: # read task
                try:
                    (addr, words) = FtdiCbmnet._cbmif_read(self)
                    self._read_queue.put((addr, words))
                    self._manager_queue.put(None)
                except TypeError: # read result is None
                    pass
            else: # write task
                (addr, words) = task
                FtdiCbmnet._cbmif_write(self, addr, words)
            self._manager_queue.task_done()

