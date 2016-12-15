from collections import defaultdict
import logging
import queue
import threading
import time


class IndexQueue:
    "Thread-safe dictionary-like (used for register file reading)."
    def __init__(self):
        self.data = defaultdict(queue.Queue)
        self.create_queue_lock = threading.Lock()

    def put(self, key, value):
        with self.create_queue_lock:
            self.data[key].put(value)

    def get(self, key, timeout=None):
        with self.create_queue_lock:
            q = self.data[key]
        try:
            value = q.get(timeout=timeout)
        except queue.Empty:
            raise IOError("could not read %X" % key)
        return value

    def clear(self, key):
        if not key in self.data:
            return
        while not self.data[key].empty():
            self.data[key].get()


class InfiniteSemaphore:
    "Fake a threading.Semaphore with infinite capacity."
    def acquire(self, blocking=None):
        if blocking is None:
            pass
        else:
            return True

    def release(self):
        pass


class StreamDemultiplexer:
    """Adaptor to convert an interface where (key, value) tuples are read and
    written sequentially to an interface where values are read from or written
    to individual keys.
    """

    WR_TASK = 0 # lower value -> higher priority
    RD_TASK = 1 # higher value -> lower priority

    def _debug(self, *text):
        _log = logging.getLogger(self.__class__.__name__)
        _log.info(' '.join(text)) # TODO use proper log levels

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
            self._comm_tasks.put(StreamDemultiplexer.WR_TASK)
            self._send_queue.task_done()

    def _read_job(self):
        """Periodically generate read tasks."""
        while not self._stop.is_set():
            self._comm_tasks.put(StreamDemultiplexer.RD_TASK)
            time.sleep(0.1)

    def _comm_job(self):
        """Process write/read tasks and put values in the receive queue."""
        while not self._stop.is_set() or not self._comm_tasks.empty():
            try:
                task = self._comm_tasks.get(timeout=0.1)
            except queue.Empty:
                continue
            if task == StreamDemultiplexer.RD_TASK:
                item = self._interface.read()
                if item is None:
                    continue
                key, value = item
                self._recv_queue[key].put(value)
            elif task == StreamDemultiplexer.WR_TASK:
                item = self._send_data.get()
                self._interface.write(item)
                self._send_data.task_done()
            if not self._stop.is_set():
                self._comm_tasks.put(StreamDemultiplexer.RD_TASK)
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


# technique shown in
# http://www.artima.com/weblogs/viewpost.jsp?thread=246483
@property
def log(self):
    return logging.getLogger(self.__class__.__name__)
