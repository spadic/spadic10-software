import threading
import Queue

# thread-safe dictionary-like (used for register file reading)
class IndexQueue:
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

