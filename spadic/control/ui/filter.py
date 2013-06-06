import curses
import mutti
from base import _SpadicPanel, SpadicDial, SpadicToggle

#--------------------------------------------------------------------

class CoeffDial(SpadicDial):
    def __init__(self, stage, *args, **kwargs):
        self.stage = stage
        SpadicDial.__init__(self, *args, **kwargs)

    def get(self):
        result = self.control_unit.get()
        coefficients = result[self.control_param]
        return coefficients[self.stage]

    def set(self):
        arg = {self.stage: self.value}
        self.control_unit.set(**{self.control_param: arg})

#--------------------------------------------------------------------

class EnableStage(SpadicToggle):
    def __init__(self, stage, *args, **kwargs):
        self.stage = stage
        SpadicToggle.__init__(self, *args, **kwargs)

    def get(self):
        result = self.control_unit.get()
        enable = result[self.control_param]
        return enable[self.stage]

    def set(self):
        arg = {self.stage: self.state}
        self.control_unit.set(**{self.control_param: arg})

#--------------------------------------------------------------------

class FilterLabel(mutti.Label):
    def __init__(self, focus_list, *args, **kwargs):
        self._focus_list = focus_list
        mutti.Label.__init__(self, *args, **kwargs)

    def _draw(self, *args):
        self.attr_ovr = (curses.A_BOLD
                         if any(p.has_focus for p in self._focus_list)
                         else 0)
        mutti.Label._draw(self, *args)

#--------------------------------------------------------------------

class FilterFrame(mutti.Frame):
    def __init__(self, spadic_controller, statusbar, _log=None):
        mutti.Frame.__init__(self, "Filter")
        self._log = _log
        u = spadic_controller.filter

        grid = mutti.Grid(3, 6)

        for col in range(2, 2+3):
            i = col-1
            d = CoeffDial(i, u, "coeffa", (-32, 31), 3,
                          "Coeff. a[%i]" % i,
                          draw_label=False, min_width=5)
            d._log = _log
            d._status = statusbar
            grid.adopt(d, 0, col)

        for col in range(1, 1+4):
            i = col-1
            d = CoeffDial(i, u, "coeffb", (-32, 31), 3,
                          "Coefficient b[%i]" % i,
                          draw_label=False, min_width=5)
            d._log = _log
            d._status = statusbar
            grid.adopt(d, 1, col)

        d = SpadicDial(u, "scaling", (-256, 255), 4, " Scaling",
                       min_width=14)
        d._log = _log
        d._status = statusbar
        grid.adopt(d, 0, 5)

        d = SpadicDial(u, "offset", (-256, 255), 4, " Offset",
                       min_width=14)
        d._log = _log
        d._status = statusbar
        grid.adopt(d, 1, 5)

        for (col, w) in zip(range(1, 1+5), [4, 4, 4, 4, 13]):
            i = col-1
            d = EnableStage(i, u, "enable",
                            ("Stage %i" % i) if i<4 else "Scaling/Offset",
                            draw_label=False, min_width=w)
            d._log = _log
            d._status = statusbar
            grid.adopt(d, 2, col)
        
        ca = [grid._panel[(0, col)] for col in range(2, 2+3)]
        L = FilterLabel(ca, "Coefficients a")
        grid.adopt(L, 0, 0)

        cb = [grid._panel[(1, col)] for col in range(1, 1+4)]
        L = FilterLabel(cb, "Coefficients b")
        grid.adopt(L, 1, 0)

        en = [grid._panel[(2, col)] for col in range(1, 1+5)]
        L = FilterLabel(en, "Enable stage")
        grid.adopt(L, 2, 0)

        self.adopt(grid)

