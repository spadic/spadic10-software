import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import Queue
import sys
import threading
import time

INF = float('inf')

from spadic import SpadicDataClient, SpadicControlClient

class SpadicDataReader:
    def __init__(self, host):
        self.dataA_client = SpadicDataClient('A', host)
        self.dataB_client = SpadicDataClient('B', host)
        self.ctrl_client = SpadicControlClient(host)

        self.period = 25-3#100e-3
        self.dlm_sent = False

        # data, mask, expiration date
        self.data_buffer = [Queue.Queue() for _ in range(32)]
        self.data_expires = [-INF for _ in range(32)]
        self.last_data = [Queue.Queue(maxsize=1) for _ in range(32)]
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
        readmethod = {'A': self.dataA_client.read_message,
                      'B': self.dataB_client.read_message}[group]
        def read_group_task():
            while not self._stop.is_set():
                m = readmethod(timeout=self.period)
                if not m or m.channel_id is None:
                    #self.ctrl_client.send_dlm(11)
                    #self.dlm_sent = True
                    continue
                t = time.time()
                c = m.channel_id + {'A': 0, 'B': 16}[group]
                if t < self.data_expires[c]:
                    continue
                mask = self.ctrl_client.control.hitlogic.read()['mask']
                if self.dlm_sent:
                    self.data_expires[c] = t
                    self.dlm_sent = False
                else:
                    self.data_expires[c] += self.period
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


def mask_to_x(mask):
    """
    Convert the encoded 32 bit mask to x values.

    Example: 0xF -> [28, 29, 30, 31]
    """
    return [31-i for i in reversed(range(32)) if (mask>>i)&1]

class SpadicDataMonitor:
    def __init__(self, spadic_data_reader):
        self.reader = spadic_data_reader
        self.period = 10e-3

        # set white background mode (must be done at the beginning)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # create window
        self.win = pg.GraphicsWindow()
        self.win.resize(1000,600)
        self.win.setWindowTitle("SPADIC Data Monitor")

        # create plot and set drawing options
        self.plot = self.win.addPlot()
        self.plot.setRange(xRange=(0, 31), yRange=(-256, 256),
                           disableAutoRange=True)
        def tickspacing(minval, maxval, size):
            return [(128, 0), (64, 0), (32, 0)]
        self.plot.getAxis('left').tickSpacing = tickspacing
        self.plot.showGrid(x=True, y=True, alpha=0.2)

        self.curve = self.plot.plot(pen='r')
        

    def run(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.gen)
        timer.start(self.period*1000) # milliseconds
        QtGui.QApplication.instance().exec_()


    def gen(self):
        """Fetch the latest data."""
        channel = 31
        try:
            (y, mask) = self.reader.last_data[channel].get(block=False)
        except Queue.Empty:
            return
        x = mask_to_x(mask)
        self.curve.setData(x, y)

    #def plot_last(self, data):
    #    """Plot the latest data and discard old data."""
    #    # keep the 9 latest lines
    #    self.lines = self.lines[:9]
    #    for (i, line) in enumerate(self.lines):
    #        line.set_color([i*0.1]*3) # newer = darker
    #        line.set_linewidth(1)
    #    # plot the newest data
    #    x, y = data
    #    if len(x) != len(y):
    #        L = min(len(x), len(y))
    #        x = x[:L]
    #        y = y[:L]
    #    newline = plt.Line2D(x, y)
    #    newline.set_color([0.8, 0.1, 0.1])
    #    newline.set_linewidth(2)
    #    self.lines.insert(0, newline)
    #    # update plot
    #    self.ax.lines = []
    #    for line in reversed(self.lines): # oldest first, newest last
    #        self.ax.add_line(line)
    #    # not sure if this is needed and what it does
    #    #return self.ax.lines


if __name__=='__main__':
    host = sys.argv[sys.argv.index('--host')+1]
    with SpadicDataReader(host) as reader:
        mon = SpadicDataMonitor(reader)
        mon.run()
        print "monitor finished"

