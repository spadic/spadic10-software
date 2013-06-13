import mutti
from filter import FilterLabel # TODO more generic name...
from base import SpadicDial, SpadicToggle

class ChannelSettingsFrame(mutti.Frame):
    def __init__(self, group, spadic_controller, statusbar, _log=None):
        mutti.Frame.__init__(self, "Channel settings")
        self.group = group
        self.control_panels = []
        self._log = _log

        upper = 3 # three rows for "upper" neighbor matrix
        lower = 3 # three rows for "lower" neighbor matrix
        col_label = 1 # one column with labels
        num_rows = upper+16+lower
        num_cols = col_label+5+upper+16+lower
        grid = mutti.Grid(num_rows, num_cols)

        t, b = 0, upper
        upper_rows = range(t, b)
        t, b = b, b+16
        channel_rows = range(t, b)
        t, b = b, b+lower 
        lower_rows = range(t, b)

        l, r = col_label, col_label+5
        setting_cols = range(l, r)
        l, r = r, r+upper
        neighbor_lower_cols = range(l, r)
        l, r = r, r+16
        neighbor_channel_cols = range(l, r)
        l, r = r, r+lower
        neighbor_lower_cols = range(l, r)

        # channel settings
        for row in channel_rows:
            i = row-upper+(16 if self.group == 'B' else 0)
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
                col = c+col_label
                d._log = _log
                d._status = statusbar
                self.control_panels.append(d)
                grid.adopt(d, row, col, update_size=False)
            
        for (col, setting) in zip(setting_cols,
         ["CSA", "  Baseline", "  ADC", "  Logic", "  Trigger"]):
            p = [grid._panel[(row, col)] for row in channel_rows]
            L = FilterLabel(p, setting)
            grid.adopt(L, 0, col, update_size=False)
            
        for row in channel_rows:
            p = [grid._panel[(row, col)] for col in range(1, 6)]
            i = row-upper
            L = FilterLabel(p, "%s.%i" % (self.group, i))

        grid.update_size()
        self.adopt(grid)

    def _set_all(self):
        for panel in self.control_panels:
            panel.set()

    def _get_all(self):
        for panel in self.control_panels:
            panel._get()

