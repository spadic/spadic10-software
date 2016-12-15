import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import queue
import scipy


def mask_to_x(mask):
    """
    Convert the encoded 32 bit mask to x values.

    Example: 0xF -> [28, 29, 30, 31]
    """
    return [31-i for i in reversed(list(range(32))) if (mask>>i)&1]


class SpadicScope:
    """
    Visualization of SpadicDataMonitor output.
    """
    def __init__(self, spadic_data_monitor, channel=31, fit=0):
        self.monitor = spadic_data_monitor
        self.channel = channel # channel 31 has injection
        self.fit = fit

        # set white background mode (must be done at the beginning)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # create window
        self.win = pg.GraphicsWindow()
        self.win.resize(400, 300)
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

        c = self.plot.plot(antialias=True)
        c.setPen(width=1, color='b')
        self.curve_res = c
        self.curves = []
        for i in reversed(list(range(10))):
            curve = self.plot.plot(antialias=True)
            if i == 0: # generated last -> on top
                curve.setPen(width=2, color='r')
            else:
                curve.setPen(width=1, color=i*0.1)
            self.curves.insert(0, curve)
        self.data = []

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
        if not self.fit:
            return data
        x, y = data
        xfit = x[:self.fit]
        yfit = y[:self.fit]

        def model(x, a, b, c, t):
            """
            Model function of the expected pulse shape.

            t is approximately 2 (shaping time divided by sampling period)
            """
            return a * np.maximum((x-b)*np.exp(-(x-b)/t), 0) + c

        popt, _ = scipy.optimize.curve_fit(model, xfit, yfit, p0=[200, 2, -100, 2])
        print(popt)
        xcorr = popt[1]-x0
        fit = model(x, *popt)
        res = np.array(y)-fit
        self.curve_res.setData([t-xcorr for t in x], res)
        return ([t-xcorr for t in x], y)

    def update_data(self):
        """Display the latest data."""
        try:
            (y, mask) = self.monitor.get_last_data(self.channel, block=False)
        except queue.Empty:
            return
        x = mask_to_x(mask)[:len(y)]
        newdata = self.correct_jitter((x, y))
        self.data = [newdata] + self.data[:9]
        for (i, data) in enumerate(self.data):
            self.curves[i].setData(*data)

