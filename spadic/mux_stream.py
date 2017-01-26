from abc import ABCMeta, abstractmethod
import logging
import queue
import threading
import time


class NoDataAvailable(Exception):
    "Raised when interfaces used by StreamDemultiplexer have no data to read."
    pass


class MultiplexedStreamInterface(metaclass=ABCMeta):
    """Representation of a streaming interface where data from different
    channels is multiplexed over a communication device which supports the
    context manager protocol.

    Concrete classes must implement write and read methods.
    """
    @abstractmethod
    def write(self, value, destination=None):
        """Write data to the communication device, consisting of a value and
        optionally the destination channel.
        """
        pass

    @abstractmethod
    def read(self):
        """Read data from the communication device and return a tuple
        (source, value).

        If no data is available to read, raise NoDataAvailable.

        Must be non-blocking.
        """
        pass


class StreamDemultiplexer:
    """Adaptor to convert a MultiplexedStreamInterface to an interface where
    values are read from or written to individual sources/destinations.
    """

    WR_TASK = 0 # lower value -> higher priority
    RD_TASK = 1 # higher value -> lower priority

    def _debug(self, *text):
        _log = logging.getLogger(type(self).__name__)
        _log.info(' '.join(text)) # TODO use proper log levels

    def __init__(self, interface, sources):
        self._interface = interface
        self._send_queue = queue.Queue()
        self._comm_tasks = queue.PriorityQueue()
        self._recv_queue = {source: queue.Queue() for source in sources}
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

    def write(self, value, destination=None):
        """Write the value to the given destination."""
        self._send_queue.put((value, destination))

    def read(self, source, timeout=1):
        """Read a value from the given source.

        If there was nothing to read, return None.
        """
        q = self._recv_queue[source]
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
                try:
                    source, value = self._interface.read()
                except NoDataAvailable:
                    continue
                self._recv_queue[source].put(value)
            elif task == StreamDemultiplexer.WR_TASK:
                value, destination = self._send_data.get()
                self._interface.write(value, destination)
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
