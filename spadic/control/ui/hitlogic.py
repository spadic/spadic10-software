import curses
import mutti
from base import _SpadicPanel, SpadicDial, SpadicToggle

#--------------------------------------------------------------------

class SelectMaskLabel(mutti.Label):
    def _draw(self, *args):
        self.attr_ovr = curses.A_BOLD if self.parent.has_focus else 0
        mutti.Label._draw(self, *args)

class SelectMaskToggle(mutti.HList, _SpadicPanel):
    def __init__(self, control_unit, control_parameter,
                       statusbar, min_width=None):
        mutti.HList.__init__(self)
        _SpadicPanel.__init__(self, control_unit, control_parameter)

        min_width = min_width or 0
        L = SelectMaskLabel("Select mask".ljust(min_width-32))
        self.adopt(L)

        self.toggles = []
        for i in range(32):
            t = mutti.Toggle("Select mask [%i]" % i, draw_label=False)
            t._status = statusbar
            t._changed = self._changed(i)
            self.toggles.append(t)
            self.adopt(t)

        self.value = self.read()
        self._decode()

    def set(self):
        self.control_unit.set(**{self.control_param: self.value})

    def _changed(self, i):
        def _changed():
            v = self.read()
            return (v>>(31-i))&1 != self.toggles[i].state
        return _changed

    def _decode(self):
        v = self.value
        for (i, t) in enumerate(reversed(self.toggles)):
            t.set_state((v>>i)&1)

    def _encode(self):
        v = sum(t.state << i
                for (i, t) in enumerate(reversed(self.toggles)))
        self.value = v
        
    def _handle_key(self, key):
        key = mutti.HList._handle_key(self, key)
        if key is not None:
            if key in self._write_keys:
                self._encode()
                self.write()
            elif key in self._read_keys:
                self.value = self.read()
                self._decode()
            else:
                return key

#--------------------------------------------------------------------

class HitLogicFrame(mutti.Frame):
    def __init__(self, spadic_controller, statusbar, _log=None):
        mutti.Frame.__init__(self, "Hit Logic")
        self._log = _log

        hitlogic_list = mutti.VList()
        hitlogic_grid = mutti.Grid(2, 2)

        u = spadic_controller.hitlogic
        for (i, d) in enumerate([
          SpadicDial(u, "threshold1", (-256, 255), 4, "Threshold 1",
                     min_width=17),                                
          SpadicDial(u, "threshold2", (-256, 255), 4, "Threshold 2",
                     min_width=17),
          SpadicDial(u, "window", (0, 63), 2, " "*5+"Hit window length",
                     min_width=27),
          SpadicToggle(u, "diffmode", " "*5+"Differential mode",
                       min_width=26),
          ]):
            d._status = statusbar
            hitlogic_grid.adopt(d, row=(i%2), col=(i//2))

        hitlogic_list.adopt(hitlogic_grid)

        selectmask = SelectMaskToggle(u, "mask", statusbar,
                                      min_width=44)
        hitlogic_list.adopt(selectmask)
        selectmask._log = _log

        self.adopt(hitlogic_list)

