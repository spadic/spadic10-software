import matplotlib.pyplot as plt
import matplotlib.animation as animation
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
                if not m or m.channel_id is None:
                    continue
                c = m.channel_id + {'A': 0, 'B': 16}[group]
                mask = self.spadic.control.hitlogic.read()['mask']
                self.data_buffer[c].put((m.data(), mask))
        return read_group_task

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if not self._stop.is_set():
            self._stop.set()
        for t in [self.groupA_reader, self.groupB_reader]:
            while t.is_alive():
                t.join(timeout=1)


def mask_to_x(mask):
    """
    Convert the encoded 32 bit mask to x values.

    Example: 0xF -> [28, 29, 30, 31]
    """
    return [31-i for i in reversed(range(32)) if (mask>>i)&1]

class SpadicDataMonitor(SpadicDataReader):
    def __init__(self, spadic):
        SpadicDataReader.__init__(self, spadic)
        #plt.ion()
        fig = plt.figure()
        self.ax = fig.add_subplot(111)
        self.ax.set_ylim(-256, 256)
        self.ax.set_xlim(0, 32)
        self.lines = self.ax.plot([], [])
        def init_func():
            return self.ax.lines
        ani = animation.FuncAnimation(fig, self.plot_last, self.gen, init_func,
                                      blit=False, interval=1, repeat=False)
        print "Press CTRL-C to exit."
        fig.show()

    def gen(self):
        channel = 0
        while True:
            try:
                (y, mask) = self.data_buffer[channel].get(timeout=1)
            except Queue.Empty:
                continue
            except KeyboardInterrupt:
                break
            x = mask_to_x(mask)
            yield (x, y)

    def plot_last(self, data):
        x, y = data
        if len(x) != len(y):
            L = min(len(x), len(y))
            x = x[:L]
            y = y[:L]
        line = plt.Line2D(x, y)
        self.lines = self.lines[-2:]+[line]
        self.ax.clear()
        for line in self.lines:
            self.ax.add_line(line)
        return self.ax.lines


if __name__=='__main__':
    import spadic
    f = open('/tmp/spadic/spadic.log', 'w')
    with spadic.Spadic(reset=1, _debug_cbmif=1, _debug_out=f) as s:
        s.control.load('datamon32.spc')
        with SpadicDataMonitor(s) as mon:
            pass

