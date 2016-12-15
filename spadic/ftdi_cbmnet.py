from . import Ftdi
from collections import namedtuple
import struct
import threading, queue
import time

# CBMnet interface packet consisting of
# addr: Address of the CBMnet send port
# words: List of 16-bit words
FtdiCbmnetPacket = namedtuple('FtdiCbmnetPacket', 'addr words')

# CBMnet interface port addresses
ADDR_DLM    = 0
ADDR_CTRL   = 1
ADDR_DATA_A = 2
ADDR_DATA_B = 3

# writable CBMnet interface ports and appropriate number of words
WRITE_LEN = {
  ADDR_DLM : 1,
  ADDR_CTRL: 3
}


class FtdiCbmnetInterface:
    """Representation of the FTDI <-> CBMnet interface."""

    from .util import log as _log
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

    def write(self, packet):
        """Write a packet to the CBMnet send interface."""
        packet = FtdiCbmnetPacket(*packet)
        if packet.addr not in WRITE_LEN:
            raise ValueError('Cannot write to this CBMnet port.')
        if len(packet.words) != WRITE_LEN[packet.addr]:
            raise ValueError('Wrong number of words for this CBMnet port.')

        self._debug('write', '%i,' % packet.addr,
                    '[%s]' % (' '.join('%04X' % w for w in packet.words)))

        header = struct.pack('BB', packet.addr, len(packet.words))
        data = struct.pack('>%dH' % len(packet.words), *packet.words)
        ftdi_data = header + data
        self._ftdi.write(ftdi_data)

    def read(self):
        """Read a packet from the CBMnet receive interface.

        If successful, return an FtdiCbmnetPacket instance.
        Otherwise, return None.
        """
        header = self._ftdi.read(2, max_iter=1)
        if len(header) < 2:
            return None

        addr, num_words = struct.unpack('BB', header)
        data = self._ftdi.read(2 * num_words)
        words = struct.unpack('>%dH' % num_words, data)

        self._debug('read', '%i,' % addr,
                    '[%s]' % (' '.join('%04X' % w for w in words)))

        return FtdiCbmnetPacket(addr, words)


WR_TASK = 0 # lower value -> higher priority
RD_TASK = 1 # higher value -> lower priority

class StreamDemultiplexer:
    """Adaptor to convert an interface where (key, value) tuples are read and
    written sequentially to an interface where values are read from or written
    to individual keys.
    """

    from .util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text)) # TODO use proper log levels

    def __init__(self, interface, keys):
        self._interface = interface
        self._send_queue = queue.Queue()
        self._comm_tasks = queue.PriorityQueue()
        self._recv_queue = {key: queue.Queue() for key in keys}
        self._send_data = queue.Queue()
        self._setup_threads()
        self._debug('init')

    def __enter__(self):
        self._interface.__enter__()
        self._start_threads()
        self._debug('enter')
        return self

    def __exit__(self, *args):
        self._stop_threads()
        self._interface.__exit__()
        self._debug('exit')

    def write(self, key, value):
        """Write the value to the given key."""
        self._send_queue.put((key, value))

    def read(self, key, timeout=1):
        """Read a value from the given key.

        If there was nothing to read, return None.
        """
        q = self._recv_queue[key]
        try:
            value = q.get(timeout=timeout)
        except queue.Empty:
            return None
        q.task_done()
        return value

    def _send_job(self):
        """Process items in the send queue."""
        while not self._stop.is_set() or not self._send_queue.empty():
            try:
                item = self._send_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            self._send_data.put(item)
            self._comm_tasks.put(WR_TASK)
            self._send_queue.task_done()

    def _read_job(self):
        """Periodically generate read tasks."""
        while not self._stop.is_set():
            self._comm_tasks.put(RD_TASK)
            time.sleep(0.1)

    def _comm_job(self):
        """Process write/read tasks and put values in the receive queue."""
        while not self._stop.is_set() or not self._comm_tasks.empty():
            try:
                task = self._comm_tasks.get(timeout=0.1)
            except queue.Empty:
                continue
            if task == RD_TASK:
                item = self._interface.read()
                if item is None:
                    continue
                key, value = item
                self._recv_queue[key].put(value)
            elif task == WR_TASK:
                item = self._send_data.get()
                self._interface.write(item)
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
        for t in list(self._threads.values()):
            t.start()
            self._debug(t.name, 'started')

    def _stop_threads(self):
        if not self._stop.is_set():
            self._stop.set()
        for t in list(self._threads.values()):
            while t.is_alive():
                t.join(timeout=1)
            self._debug(t.name, 'finished')


class FtdiCbmnet:
    """Representation of the CBMnet interface over FTDI."""

    from .util import log as _log
    def _debug(self, *text):
        self._log.info(' '.join(text)) # TODO use proper log levels

    def __init__(self):
        self._demux = StreamDemultiplexer(
            interface=FtdiCbmnetInterface(),
            keys=[ADDR_DATA_A, ADDR_DATA_B, ADDR_CTRL]
        )
        self._debug('init')

    def __enter__(self):
        self._demux.__enter__()
        self._debug('enter')
        return self

    def __exit__(self, *args):
        self._demux.__exit__()
        self._debug('exit')

    def write_ctrl(self, words):
        """Write words to the control port of the CBMnet send interface."""
        self._demux.write(ADDR_CTRL, words)

    def write_command(self, words):
        """Write words to the command port of the CBMnet send interface."""
        self._demux.write(ADDR_DLM, words)

    def read_data(self, lane, timeout=1):
        """Read words from the CBMnet data receive interface at the given lane
        number.
        """
        addr = [ADDR_DATA_A, ADDR_DATA_B][lane]
        return self._demux.read(addr, timeout)

    def read_ctrl(self, timeout=1):
        """Read words from the CBMnet control receive interface."""
        return self._demux.read(ADDR_CTRL, timeout)
