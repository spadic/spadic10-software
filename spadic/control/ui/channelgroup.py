import mutti
from filter import FilterLabel # TODO more generic name...
from base import SpadicDial, SpadicToggle

class ChannelSettingsFrame(mutti.Frame):
    def __init__(self, group, spadic_controller, statusbar, _log=None):
        mutti.Frame.__init__(self, "Channel settings")
        self.group = group
        self.control_panels = []
        self._log = _log

        row_off = 1
        col_off = 1
        num_rows = row_off+16
        num_cols = col_off+5
        channel_rows = range(row_off, row_off+16)
        setting_cols = range(col_off, col_off+5)
        grid = mutti.Grid(num_rows, num_cols)

        for row in channel_rows:
            i = row-row_off+(16 if self.group == 'B' else 0)
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
                col = c+col_off
                d._log = _log
                d._status = statusbar
                self.control_panels.append(d)
                grid.adopt(d, row, col)
            
        for (col, setting) in zip(setting_cols,
         ["CSA", "  Baseline", "  ADC", "  Logic", "  Trigger"]):
            p = [grid._panel[(row, col)] for row in channel_rows]
            L = FilterLabel(p, setting)
            grid.adopt(L, 0, col)
            
        for row in channel_rows:
            p = [grid._panel[(row, col)] for col in range(1, 6)]
            i = row-row_off
            L = FilterLabel(p, "%s.%i" % (self.group, i))
            grid.adopt(L, row, 0)

        self.adopt(grid)

    def _set_all(self):
        for panel in self.control_panels:
            panel.set()

    def _get_all(self):
        for panel in self.control_panels:
            panel._get()

