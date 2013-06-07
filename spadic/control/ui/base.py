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
        
#--------------------------------------------------------------------

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

    def _get(self):
        self.set_value(self.get())
        
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
        
#--------------------------------------------------------------------

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

    def _get(self):
        self.set_state(self.get())
        
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

