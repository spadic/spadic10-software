import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import Queue
import scipy
import sys
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


def mask_to_x(mask):
    """
    Convert the encoded 32 bit mask to x values.

    Example: 0xF -> [28, 29, 30, 31]
    """
    return [31-i for i in reversed(range(32)) if (mask>>i)&1]


class SpadicScope:
    """
    Visualization of SpadicDataMonitor output.
    """
    def __init__(self, spadic_data_monitor, channel=0):
        self.monitor = spadic_data_monitor
        self.channel = channel

        # set white background mode (must be done at the beginning)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # create window
        self.win = pg.GraphicsWindow()
        self.win.resize(400,300)
        self.win.setWindowTitle("SPADIC Data Monitor")

        # create plot and set drawing options
        self.plot = self.win.addPlot()
        self.plot.setRange(xRange=(0, 32), yRange=(-256, 256),
                           disableAutoRange=True)
        def ytickspacing(minval, maxval, size):
            return [(128, 0), (64, 0), (32, 0)]
        def xtickspacing(minval, maxval, size):
            return [(8, 0), (4, 0), (1, 0)]
        self.plot.getAxis('left').tickSpacing = ytickspacing
        self.plot.getAxis('bottom').tickSpacing = xtickspacing
        self.plot.showGrid(x=True, y=True, alpha=0.2)

        self.curves = []
        for i in reversed(range(10)):
            curve = self.plot.plot(antialias=True)
            if i == 0: # generated last -> on top
                curve.setPen(width=2, color='r')
            else:
                curve.setPen(width=1, color=i*0.1)
            self.curves.insert(0, curve)
        self.data = []

        def model(x, a, b, c, t):
            """
            Model function of the expected pulse shape.

            t is approximately 2 (shaping time divided by sampling period)
            """
            return a * np.maximum((x-b)*np.exp(-(x-b)/t), 0) + c
        self.model = model

    def run(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update_data)
        timer.start(self.monitor._period*1000) # milliseconds
        QtGui.QApplication.instance().exec_()

    def correct_jitter(self, data, x0=2):
        """
        Remove horizontal fluctuation of the curves.

        Detect and move the rise of the pulse (b parameter in the model
        function). By default, the rise of the pulse is moved to position 2.
        """
        x, y = data
        popt, _ = scipy.optimize.curve_fit(self.model, x, y, p0=[100, 0, 0, 2])
        print popt
        xcorr = popt[1]-x0
        return ([t-xcorr for t in x], y)

    def update_data(self):
        """Display the latest data."""
        try:
            (y, mask) = self.monitor.get_last_data(self.channel, block=False)
        except Queue.Empty:
            return
        x = mask_to_x(mask)
        self.data = [self.correct_jitter((x, y))] + self.data[:9]
        for (i, data) in enumerate(self.data):
            self.curves[i].setData(*data)



if __name__=='__main__':
    host = sys.argv[sys.argv.index('--host')+1]
    with SpadicDataMonitor(host) as mon:
        scope = SpadicScope(mon, channel=31)
        scope.run()

