import Ftdi
import struct
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


class FtdiCbmnetInterface:
    """Wrapper for FTDI <-> CBMnet interface communication."""

    from util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text)) # TODO use proper log levels

    def __init__(self):
        """Prepare FTDI connection."""
        self._ftdi = Ftdi.Ftdi()
        self._debug('init')

    def __enter__(self):
        """Open FTDI connection."""
        self._ftdi.__enter__()
        self._debug('enter')
        return self

    def __exit__(self, *args):
        """Close FTDI connection."""
        self._ftdi.__exit__(*args)
        self._debug('exit')

    def write(self, addr, words):
        """Access CBMnet send interface through FTDI write port.

        addr: Address of the CBMnet send port
        words: List of 16-bit words to be sent

        This method builds a data packet for the CBMnet send interface and
        transfers the individual bytes in the correct order through the
        FTDI write port.
        """
        if addr not in WRITE_LEN:
            raise ValueError('Cannot write to this CBMnet port.')
        if len(words) != WRITE_LEN[addr]:
            raise ValueError('Wrong number of words for this CBMnet port.')

        self._debug('write', '%i,' % addr,
                    '[%s]' % (' '.join('%04X' % w for w in words)))

        header = struct.pack('BB', addr, len(words))
        data = struct.pack('>%dH' % len(words), *words)
        ftdi_data = header + data
        self._ftdi.write(ftdi_data)


    def read(self):
        """Access CBMnet receive interface through FTDI read port.

        This method tries to read data from the FTDI and reconstruct a
        packet from the CBMnet receive interface.

        If successful, it returns a tuple (addr, words):
        addr: Address of the CBMnet receive port
        words: List of received 16-bit words

        Otherwise, it does not block, but return None instead.
        """
        header = self._ftdi.read(2, max_iter=1)
        if len(header) < 2:
            return None

        addr, num_words = struct.unpack('BB', header)
        data = self._ftdi.read(2 * num_words)
        words = struct.unpack('>%dH' % num_words, data)

        self._debug('read', '%i,' % addr,
                    '[%s]' % (' '.join('%04X' % w for w in words)))

        return addr, words


WR_TASK = 0 # lower value -> higher priority
RD_TASK = 1 # higher value -> lower priority

class FtdiCbmnet:
    """FTDI <-> CBMnet interface communication with threads."""

    from util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text)) # TODO use proper log levels

    def __init__(self):
        self._interface = FtdiCbmnetInterface()
        self._send_queue = Queue.Queue()
        self._comm_tasks = Queue.PriorityQueue()
        self._recv_queue = {addr: Queue.Queue()
                            for addr in (ADDR_DATA_A, ADDR_DATA_B, ADDR_CTRL)}
        self._send_data = Queue.Queue()
        self._setup_threads()
        self._debug('init')


    def __enter__(self):
        self._interface.__enter__()
        self._start_threads()
        self._debug('enter')
        return self

    def __exit__(self, *args):
        """Bring all threads to halt."""
        self._stop_threads()
        self._interface.__exit__()
        self._debug('exit')

    #--------------------------------------------------------------------
    # overwrite the non-threaded user interface
    #--------------------------------------------------------------------
    def write(self, addr, words):
        """Write words to the CBMnet send interface."""
        self._send_queue.put((addr, words))

    def read(self, addr, timeout=1):
        """Read words from the CBMnet receive interface.

        If there was nothing to read, return None.
        """
        q = self._recv_queue[addr]
        try:
            words = q.get(timeout=timeout)
        except Queue.Empty:
            return None
        q.task_done()
        return words

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
                    (addr, words) = self._interface.read()
                except TypeError: # read result is None
                    continue
                self._recv_queue[addr].put(words)
            elif task == WR_TASK:
                (addr, words) = self._send_data.get()
                self._interface.write(addr, words)
                self._send_data.task_done()
            if not self._stop.is_set():
                self._comm_tasks.put(RD_TASK)
            self._comm_tasks.task_done()

    def _setup_threads(self):
        self._stop = threading.Event()

        names = ['send worker', 'read worker', 'comm worker']
        jobs = [self._send_job, self._read_job, self._comm_job]
        self._threads = {n: threading.Thread(name=n) for n in names}

        for name, job in zip(names, jobs):
            t = self._threads[name]
            t.run = job
            t.daemon = True

    def _start_threads(self):
        for t in self._threads.values():
            t.start()
            self._debug(t.name, 'started')

    def _stop_threads(self):
        if not self._stop.is_set():
            self._stop.set()
        for t in self._threads.values():
            while t.is_alive():
                t.join(timeout=1)
            self._debug(t.name, 'finished')
