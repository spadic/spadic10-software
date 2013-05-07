import threading

# thread-safe dictionary-like (used for register file reading)
class IndexQueue:
    def __init__(self):
        self.data = {}
        self.requests = {}
        self.data_lock = threading.Lock()
        self.requests_lock = threading.Lock()

    def put(self, key, value):
        with self.data_lock:
            self.data[key] = value
        with self.requests_lock:
            if key not in self.requests:
                self.requests[key] = threading.Event()
            self.requests[key].set()

    def get(self, key):
        with self.requests_lock:
            if key not in self.requests:
                self.requests[key] = threading.Event()
            r = self.requests[key]
        r.wait()
        with self.requests_lock:
            self.requests[key].clear()
        with self.data_lock:
            value = self.data[key]
            del self.data[key]
            return value

