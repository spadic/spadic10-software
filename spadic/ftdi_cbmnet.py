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

    def __init__(self, _debug_out=None):
        Ftdi.Ftdi.__init__(self, _debug_out=_debug_out)
        self._debug_cbmif = False


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

        if self._debug_cbmif:
            self._debug("CBMnet write " +
                "%i"%addr + ", ["+" ".join("%X"%w for w in words)+"]")

        header = [addr, len(words)]
        data = []
        for w in words:
            high, low = w//0x100, w%0x100
            data.append(high)
            data.append(low)
        ftdi_data = header + data
        self._ftdi_write(ftdi_data)


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

        if self._debug_cbmif:
            self._debug("CBMnet  read " +
                "%i"%addr + ", ["+" ".join("%X"%w for w in words)+"]")

        return (addr, words)


WR_TASK = 0 # higher priority
RD_TASK = 1 # lower priority

class FtdiCbmnetThreaded(FtdiCbmnet):
    """FTDI <-> CBMnet interface communication with threads."""

    def __init__(self, _debug_out=None):
        FtdiCbmnet.__init__(self, _debug_out)

        # set up threads and queues
        self._stop = threading.Event()

        self._send_queue = Queue.Queue()
        self._send_worker = threading.Thread(name="send worker")
        self._send_worker.run = self._send_job
        self._send_worker.daemon = True

        self._read_worker = threading.Thread(name="read worker")
        self._read_worker.run = self._read_job
        self._read_worker.daemon = True

        self._comm_tasks = Queue.PriorityQueue()
        self._send_data = Queue.Queue()
        self._recv_queue = Queue.Queue()
        self._comm_worker = threading.Thread(name="comm worker")
        self._comm_worker.run = self._comm_job
        self._comm_worker.daemon = True

        # start threads
        self._send_worker.start()
        self._read_worker.start()
        self._comm_worker.start()

    def __del__(self):
        self.__exit__()


    #--------------------------------------------------------------------
    # support "with" statement -> __exit__ is guaranteed to be called
    #--------------------------------------------------------------------
    def __exit__(self, *args):
        """Bring all threads to halt."""
        if not self._stop.is_set():
            self._stop.set()
        for w in [self._send_worker, self._read_worker, self._comm_worker]:
            w.join()
            if self._debug_cbmif:
                self._debug(w.name, "finished")
        FtdiCbmnet.__exit__(self)


    #--------------------------------------------------------------------
    # overwrite the user interface
    #--------------------------------------------------------------------
    def _cbmif_write(self, addr, words):
        """Write words to the CBMnet send interface."""
        self._send_queue.put((addr, words))

    def _cbmif_read(self):
        """Read words from the CBMnet receive interface.
        
        If there was nothing to read, return None.
        """
        try:
            (addr, words) = self._recv_queue.get(timeout=0.1)
        except Queue.Empty:
            return None
        self._recv_queue.task_done()
        return (addr, words)


    #--------------------------------------------------------------------
    # The following methods are run in separate threads and connect
    # overwritten user interface methods to the original methods.
    #
    # The read operation is triggered by three sources:
    # - after each write operation
    # - after each successful read operation
    # - periodically every 0.1 seconds
    #--------------------------------------------------------------------
    def _send_job(self):
        """Process objects in the send queue."""
        while not self._stop.is_set() or not self._send_queue.empty():
            try:
                (addr, words) = self._send_queue.get(timeout=0.1)
            except Queue.Empty:
                continue
            self._send_data.put((addr, words))
            self._comm_tasks.put(WR_TASK)
            self._send_queue.task_done()

    def _read_job(self):
        """Periodically generate read tasks."""
        while not self._stop.is_set():
            self._comm_tasks.put(RD_TASK)
            time.sleep(0.1)
                
    def _comm_job(self):
        """Process write/read tasks and put data in the receive queue."""
        while not self._stop.is_set() or not self._comm_tasks.empty():
            try:
                task = self._comm_tasks.get(timeout=0.1)
            except Queue.Empty:
                continue
            if task == RD_TASK:
                try:
                    (addr, words) = FtdiCbmnet._cbmif_read(self)
                except TypeError: # read result is None
                    continue
                self._recv_queue.put((addr, words))
            elif task == WR_TASK:
                (addr, words) = self._send_data.get()
                FtdiCbmnet._cbmif_write(self, addr, words)
                self._send_data.task_done()
            if not self._stop.is_set():
                self._comm_tasks.put(RD_TASK)
            self._comm_tasks.task_done()

