import matplotlib.pyplot as plt
import threading
import Queue

class SpadicDataReader:
    def __init__(self, spadic):
        self.spadic = spadic
        self.data_buffer = [Queue.Queue() for _ in range(32)]
        self._stop = threading.Event()
        self.groupA_reader = threading.Thread(name="groupA_reader")
        self.groupB_reader = threading.Thread(name="groupB_reader")
        self.groupA_reader.run = self._read_group_task('A')
        self.groupB_reader.run = self._read_group_task('B')
        self.groupA_reader.daemon = True
        self.groupB_reader.daemon = True
        self.groupA_reader.start()
        self.groupB_reader.start()

    def _read_group_task(self, group):
        readmethod = {'A': self.spadic.read_groupA,
                      'B': self.spadic.read_groupB}[group]
        def read_group_task():
            while not self._stop.is_set():
                m = readmethod()
                if not m:
                    continue
                c = m.channel_id + {'A': 0, 'B': 16}[group]
                mask = self.spadic.control.hitlogic.read()['mask']
                self.data_buffer[c].put((m.data(), mask))
        return read_group_task

    def __exit__(self):
        if not self._stop.is_set():
            self._stop.set()
        for t in [self.groupA_reader, self.groupB_reader]:
            t.join()


def mask_to_x(mask):
    """
    Convert the encoded 32 bit mask to x values.

    Example: 0xF -> [28, 29, 30, 31]
    """
    return [31-i for i in reversed(range(32)) if (mask>>i)&1]

class SpadicDataMonitor(SpadicDataReader):
    def __init__(self, *args, **kwargs):
        SpadicDataReader.__init__(self, *args, **kwargs)
        plt.ion()
        fig = plt.figure()
        self.ax = fig.add_subplot(111)

    def plot_last(self, channel):
        if self.data_buffer[channel].empty():
            raise RuntimeError("no data for channel %i" % channel)
        (data, mask) = self.data_buffer[channel].get()
        x = mask_to_x(mask)
        self.ax.plot(x, data)
        plt.show()

