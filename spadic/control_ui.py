import curses
import curses.ascii
import mutti

class _SpadicPanel:
    _write_keys = [ord('p'), curses.ascii.LF]
    _read_keys  = [ord('r'), curses.KEY_BACKSPACE]

    def __init__(self, control_unit, control_param):
        self.control_unit = control_unit
        self.control_param = control_param

    def apply(self):
        self.control_unit.apply()

    def write(self):
        self.set()
        self.apply()

    def get(self):
        result = self.control_unit.get()
        return result[self.control_param]

    def update(self):
        self.control_unit.update()

    def read(self):
        self.update()
        return self.get()
        

class SpadicDial(_SpadicPanel, mutti.Dial):
    def __init__(self, control_unit, control_param, *args, **kwargs):
        """
        Connect the graphical with the functional control.

        E.g. SpadicDial(c.hitlogic, "threshold1", ...)
        """
        mutti.Dial.__init__(self, *args, **kwargs)
        _SpadicPanel.__init__(self, control_unit, control_param)
        mutti.Dial.set_value(self, self.read())

    def set(self):
        self.control_unit.set(**{self.control_param: self.value})
        
    def _handle_key(self, key):
        key = mutti.Dial._handle_key(self, key)
        if key is not None:
            if key in self._write_keys:
                self.write()
            elif key in self._read_keys:
                self.set_value(self.read())
            else:
                return key

    def _changed(self):
        return self.read() != self.value
        

class SpadicToggle(_SpadicPanel, mutti.Toggle):
    def __init__(self, control_unit, control_param, *args, **kwargs):
        """
        Connect the graphical with the functional control.

        E.g. SpadicToggle(c.hitlogic, "diffmode", ...)
        """
        mutti.Toggle.__init__(self, *args, **kwargs)
        _SpadicPanel.__init__(self, control_unit, control_param)
        mutti.Toggle.set_state(self, self.read())

    def set(self):
        self.control_unit.set(**{self.control_param: self.state})
        
    def _handle_key(self, key):
        key = mutti.Toggle._handle_key(self, key)
        if key is not None:
            if key in self._write_keys:
                self.write()
            elif key in self._read_keys:
                self.set_state(self.read())
            else:
                return key

    def _changed(self):
        return self.read() != self.state
        
#--------------------------------------------------------------------

class SelectMaskLabel(mutti.Label):
    def __init__(self, *args, **kwargs):
        mutti.Label.__init__(self, *args, **kwargs)
        self.attr_ovr = 0

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

class SpadicControlUI(mutti.Screen):
    def __init__(self, spadic_controller, _log=None):
        mutti.Screen.__init__(self)
        c = spadic_controller
        self._log = _log

        tabs = mutti.Tabs()
        tabs._log = _log

        # Hit Logic + DLM trigger settings
        hitlogic_dlm_list = mutti.VList()
        u = c.hitlogic

        hitlogic_frame = mutti.Frame("Hit Logic")
        hitlogic_list = mutti.VList()

        hitlogic_grid = mutti.Grid(2, 2)
        for (i, d) in enumerate([
          SpadicDial(u, "threshold1", "Threshold 1", (-256, 255), 4,
                     min_width=17),
          SpadicDial(u, "threshold2", "Threshold 2", (-256, 255), 4,
                     min_width=17),
          SpadicDial(u, "window", " "*5+"Hit window length", (0, 63), 2,
                     min_width=27),
          SpadicToggle(u, "diffmode", " "*5+"Differential mode",
                       min_width=26),
          ]):
            d._status = self.statusbar
            hitlogic_grid.adopt(d, row=(i%2), col=(i//2))

        hitlogic_list.adopt(hitlogic_grid)

        selectmask = SelectMaskToggle(u, "mask", self.statusbar,
                                      min_width=44)
        hitlogic_list.adopt(selectmask)
        selectmask._log = _log

        hitlogic_frame.adopt(hitlogic_list)
        hitlogic_dlm_list.adopt(hitlogic_frame)

        dlm_frame = mutti.Frame("DLM Trigger")
        dlm_list = mutti.VList()
        for d in [SpadicToggle(u, "analogtrigger", "Analog trigger",
                               min_width=20),
                  SpadicToggle(u, "triggerout", "Trigger output",
                               min_width=20),
                 ]:
            d._status = self.statusbar
            dlm_list.adopt(d)
        dlm_frame.adopt(dlm_list)
        hitlogic_dlm_list.adopt(dlm_frame)

        tabs.adopt(hitlogic_dlm_list, "Global digital settings")
        self.adopt(tabs)

