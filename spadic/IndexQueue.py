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
            if not key in self.data:
                self.data[key] = []
            self.data[key].append(value)
        with self.requests_lock:
            if key not in self.requests:
                self.requests[key] = threading.Semaphore(0)
            r = self.requests[key]
        r.release()

    def get(self, key):
        with self.requests_lock:
            if key not in self.requests:
                self.requests[key] = threading.Semaphore(0)
            r = self.requests[key]
        r.acquire()
        with self.data_lock:
            value = self.data[key].pop(0)
        return value

