import mutti
from base import SpadicDial

class AdcBiasFrame(mutti.Frame):
    def __init__(self, spadic_controller, statusbar, _log=None):
        mutti.Frame.__init__(self, "ADC Bias")
        self.control_panels = []
        self._log = _log

        grid = mutti.Grid(2, 3)

        u = spadic_controller.adcbias
        for (i, d) in enumerate([
          SpadicDial(u, "vndel", (0, 127), 3, "VNDel",
                     min_width=15),                                
          SpadicDial(u, "vpdel", (0, 127), 3, "VPDel",
                     min_width=15),                                
          SpadicDial(u, "vploadfb", (0, 127), 3, " VPLoadFB",
                     min_width=15),                                
          SpadicDial(u, "vploadfb2", (0, 127), 3, " VPLoadFB2",
                     min_width=15),                                
          SpadicDial(u, "vpfb", (0, 127), 3, " VPFB",
                     min_width=15),                                
          SpadicDial(u, "vpamp", (0, 127), 3, " VPAmp",
                     min_width=15),                                
          ]):
            d._status = statusbar
            d._log = _log
            self.control_panels.append(d)
            grid.adopt(d, row=(i%2), col=(i//2))

        self.adopt(grid)

    def _set_all(self):
        for panel in self.control_panels:
            panel.set()

    def _get_all(self):
        for panel in self.control_panels:
            panel._get()

