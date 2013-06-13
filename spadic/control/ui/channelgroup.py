import mutti
from filter import FilterLabel # TODO more generic name...
from base import SpadicDial, SpadicToggle

class NeighborMatrixToggle(SpadicToggle):
    def __init__(self, source_ch, target_ch, control_unit, *args, **kwargs):
        self._source_ch = source_ch
        self._target_ch = target_ch
        SpadicToggle.__init__(self, control_unit, '', *args, **kwargs)

    def set(self):
        args = {'source': self._source_ch, 'target': self._target_ch,
                'enable': self.state}
        self.control_unit.set(**args)

    def get(self):
        result = self.control_unit.get()
        tgt = self._target_ch
        return (tgt in result and
                self._source_ch in result[tgt])

class ChannelSettingsFrame(mutti.Frame):
    def __init__(self, group, spadic_controller, statusbar, _log=None):
        mutti.Frame.__init__(self, "Channel settings & Neighbor trigger")
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
        neighbor_upper_cols = range(l, r)
        l, r = r, r+16
        neighbor_channel_cols = range(l, r)
        l, r = r, r+lower
        neighbor_lower_cols = range(l, r)

        g = self.group
        # channel settings
        for row in channel_rows:
            i = row-upper+(16 if g == 'B' else 0)
            u_ana = spadic_controller.frontend.channel[i]
            u_dig = spadic_controller.digital.channel[i]
            for (c, d) in enumerate([
              SpadicToggle(u_ana, "enablecsa",
                           "CSA [%s.%i]" % (g, i%16),
                           draw_label=False, min_width=3),
              SpadicDial(u_ana, "baseline", (0, 127), 3,
                           "Baseline trim [%s.%i]" % (g, i%16),
                           draw_label=False, min_width=9),
              SpadicToggle(u_ana, "enableadc",
                           "ADC [%s.%i]" % (g, i%16),
                           draw_label=False, min_width=5),
              SpadicToggle(u_dig, "enable",
                           "Logic [%s.%i]" % (g, i%16),
                           draw_label=False, min_width=7),
              SpadicToggle(u_dig, "entrigger",
                           "Trigger input [%s.%i]" % (g, i%16),
                           draw_label=False, min_width=8),
              ]):
                col = c+col_label
                d._log = _log
                d._status = statusbar
                self.control_panels.append(d)
                grid.adopt(d, row, col, update_size=False)

        # neighbor matrix
        u = spadic_controller.digital.neighbor[g]
        # -- channels -> upper
        for row in upper_rows:
            for col in neighbor_channel_cols:
                src = col-col_label-5-lower
                tgt = "U%i"%row
                s = "%s.%i -> %s.%s" % (g, src, g, tgt)
                t = NeighborMatrixToggle(src, tgt, u, 
                     "Neighbor trigger [%s]"%s, draw_label=False)
                t._status = statusbar
                t._log = _log
                self.control_panels.append(t)
                grid.adopt(t, row, col, update_size=False)
        # -- channels -> channels
        for row in channel_rows:
            for col in neighbor_channel_cols:
                src = col-col_label-5-lower
                tgt = row-lower
                if not src == tgt:
                    s = "%s.%i -> %s.%i" % (g, src, g, tgt)
                    t = NeighborMatrixToggle(src, tgt, u,
                         "Neighbor trigger [%s]"%s, draw_label=False)
                    t._status = statusbar
                    t._log = _log
                    self.control_panels.append(t)
                    grid.adopt(t, row, col, update_size=False)
        # -- channels -> lower
        for row in lower_rows:
            for col in neighbor_channel_cols:
                src = col-col_label-5-lower
                tgt = "L%i"%(row-lower-16)
                s = "%s.%i -> %s.%s" % (g, src, g, tgt)
                t = NeighborMatrixToggle(src, tgt, u,
                     "Neighbor trigger [%s]"%s, draw_label=False)
                t._status = statusbar
                t._log = _log
                self.control_panels.append(t)
                grid.adopt(t, row, col, update_size=False)
        # -- upper -> channels
        for row in channel_rows:
            for col in neighbor_upper_cols:
                src = "U%i"%(col-col_label-5)
                tgt = row-lower
                s = "%s.%s -> %s.%i" % (g, src, g, tgt)
                t = NeighborMatrixToggle(src, tgt, u,
                     "Neighbor trigger [%s]"%s, draw_label=False)
                t._status = statusbar
                t._log = _log
                self.control_panels.append(t)
                grid.adopt(t, row, col, update_size=False)
        # -- lower -> channels
        for row in channel_rows:
            for col in neighbor_lower_cols:
                src = "L%i"%(col-col_label-5-upper-16)
                tgt = row-lower
                s = "%s.%s -> %s.%i" % (g, src, g, tgt)
                t = NeighborMatrixToggle(src, tgt, u,
                     "Neighbor trigger [%s]"%s, draw_label=False)
                t._status = statusbar
                t._log = _log
                self.control_panels.append(t)
                grid.adopt(t, row, col, update_size=False)
            
        # labels
        for (col, setting) in zip(setting_cols,
         ["  CSA", "  Baseline", "  ADC", "  Logic", "  Trigger  "]):
            p = [grid._panel[(row, col)] for row in channel_rows]
            L = FilterLabel(p, setting)
            grid.adopt(L, 0, col, update_size=False)
        for row in channel_rows:
            p = [grid._panel[(row, col)] for col in
                 setting_cols + neighbor_lower_cols +
                                neighbor_channel_cols +
                                neighbor_upper_cols
                 if (row, col) in grid._panel]
            i = row-upper
            L = FilterLabel(p, "%s.%i" % (g, i))
            grid.adopt(L, row, 0, update_size=False)
        for row in upper_rows:
            p = [grid._panel[(row, col)] for col in neighbor_channel_cols]
            s = "U%i"%row
            L = FilterLabel(p, "%s.%s" % (g, s))
            grid.adopt(L, row, 0, update_size=False)
        for row in lower_rows:
            p = [grid._panel[(row, col)] for col in neighbor_channel_cols]
            s = "L%i"%(row-upper-16)
            L = FilterLabel(p, "%s.%s" % (g, s))
            grid.adopt(L, row, 0, update_size=False)
            
        grid.update_size()
        self.adopt(grid)

    def _set_all(self):
        for panel in self.control_panels:
            panel.set()

    def _get_all(self):
        for panel in self.control_panels:
            panel._get()

