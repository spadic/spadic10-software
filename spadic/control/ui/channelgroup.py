import mutti
from filter import FilterLabel # TODO more generic name...
from base import SpadicDial, SpadicToggle

class ChannelSettingsFrame(mutti.Frame):
    def __init__(self, group, spadic_controller, statusbar, _log=None):
        mutti.Frame.__init__(self, "Channel settings")
        self.group = group
        self.control_panels = []
        self._log = _log

        rows = 17 # 16+1
        cols = 6  # 5+1
        grid = mutti.Grid(rows, cols)

        for row in range(1, 17):
            i = row-1+(16 if self.group == 'B' else 0)
            u_ana = spadic_controller.frontend.channel[i]
            u_dig = spadic_controller.digital.channel[i]
            for (c, d) in enumerate([
              SpadicToggle(u_ana, "enablecsa",
                           "CSA [%s.%i]" % (self.group, i%16),
                           draw_label=False, min_width=5),
              ]):
                col = c+1
                d._log = _log
                d._status = statusbar
                self.control_panels.append(d)
                grid.adopt(d, row, col)

        self.adopt(grid)

    def _set_all(self):
        for panel in self.control_panels:
            panel.set()

    def _get_all(self):
        for panel in self.control_panels:
            panel._get()

