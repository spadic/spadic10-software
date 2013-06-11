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
                           draw_label=False, min_width=3),
              SpadicDial(u_ana, "baseline", (0, 127), 3,
                           "Baseline trim [%s.%i]" % (self.group, i%16),
                           draw_label=False, min_width=9),
              SpadicToggle(u_ana, "enableadc",
                           "ADC [%s.%i]" % (self.group, i%16),
                           draw_label=False, min_width=5),
              SpadicToggle(u_dig, "enable",
                           "Logic [%s.%i]" % (self.group, i%16),
                           draw_label=False, min_width=7),
              SpadicToggle(u_dig, "entrigger",
                           "Trigger input [%s.%i]" % (self.group, i%16),
                           draw_label=False, min_width=8),
              ]):
                col = c+1
                d._log = _log
                d._status = statusbar
                self.control_panels.append(d)
                grid.adopt(d, row, col)
            
        p = [grid._panel[(row, 1)] for row in range(1, 17)]
        L = FilterLabel(p, "CSA")
        grid.adopt(L, 0, 1)
            
        p = [grid._panel[(row, 2)] for row in range(1, 17)]
        L = FilterLabel(p, "  Baseline")
        grid.adopt(L, 0, 2)
            
        p = [grid._panel[(row, 3)] for row in range(1, 17)]
        L = FilterLabel(p, "  ADC")
        grid.adopt(L, 0, 3)
            
        p = [grid._panel[(row, 4)] for row in range(1, 17)]
        L = FilterLabel(p, "  Logic")
        grid.adopt(L, 0, 4)
            
        p = [grid._panel[(row, 5)] for row in range(1, 17)]
        L = FilterLabel(p, "  Trigger")
        grid.adopt(L, 0, 5)

        for row in range(1, 17):
            p = [grid._panel[(row, col)] for col in range(1, 6)]
            i = row-1
            L = FilterLabel(p, "%s.%i" % (self.group, i))
            grid.adopt(L, row, 0)

        self.adopt(grid)

    def _set_all(self):
        for panel in self.control_panels:
            panel.set()

    def _get_all(self):
        for panel in self.control_panels:
            panel._get()

