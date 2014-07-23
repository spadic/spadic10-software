import logging
import threading
import Queue


class IndexQueue:
    "Thread-safe dictionary-like (used for register file reading)."
    def __init__(self):
        self.data = {}
        self.data_lock = threading.Lock()

    def put(self, key, value):
        with self.data_lock:
            if not key in self.data:
                self.data[key] = Queue.Queue()
        self.data[key].put(value)

    def get(self, key, timeout=None):
        with self.data_lock:
            if not key in self.data:
                self.data[key] = Queue.Queue()
        try:
            value = self.data[key].get(timeout=timeout)
        except Queue.Empty:
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


# technique shown in
# http://www.artima.com/weblogs/viewpost.jsp?thread=246483
@property
def log(self):
    return logging.getLogger(self.__class__.__name__)

