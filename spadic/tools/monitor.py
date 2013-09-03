import Queue
import threading
import time

INF = float('inf')

from spadic import SpadicDataClient, SpadicControlClient


class SpadicDataMonitor:
    """
    Continuously reads data, discarding any messages that come faster than
    the specified rate.
    """
    def __init__(self, host, rate=60):
        self.dataA_client = SpadicDataClient('A', host)
        self.dataB_client = SpadicDataClient('B', host)
        self.ctrl_client = SpadicControlClient(host)

        self._period = 1.0/rate

        # data, mask, expiration date
        self.data_buffer = [Queue.Queue() for _ in range(32)]
        self.data_expires = [-INF for _ in range(32)]
        self.last_data = [Queue.Queue(maxsize=1) for _ in range(32)]
        self._stop = threading.Event()
        self.groupA_reader = threading.Thread(name="groupA_reader")
        self.groupB_reader = threading.Thread(name="groupB_reader")
        self.groupA_reader.run = self._read_group_task('A')
        self.groupB_reader.run = self._read_group_task('B')
        self.groupA_reader.start()
        self.groupB_reader.start()

    def _read_group_task(self, group):
        readmethod = {'A': self.dataA_client.read_message,
                      'B': self.dataB_client.read_message}[group]
        def read_group_task():
            while not self._stop.is_set():
                m = readmethod(timeout=self._period)
                t = time.time()
                if not m or m.channel_id is None:
                    continue
                c = m.channel_id + {'A': 0, 'B': 16}[group]
                if t < self.data_expires[c]:
                    continue # data not yet expired
                self.data_expires[c] = t + self._period
                mask = self.ctrl_client.control.hitlogic.read()['mask']
                if self.last_data[c].full():
                    try:
                        self.last_data[c].get(block=False)
                    except Queue.Empty:
                        pass
                self.last_data[c].put((m.data(), mask))
        return read_group_task

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if not self._stop.is_set():
            self._stop.set()
        for t in [self.groupA_reader, self.groupB_reader]:
            while t.is_alive():
                t.join(timeout=1)

    def get_last_data(self, channel, **queue_args):
        """Get the latest data of one channel."""
        return self.last_data[channel].get(**queue_args)


