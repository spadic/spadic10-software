import curses
import mutti

class SpadicControlDial(mutti.Dial):
    def __init__(self, control_unit, control_param, *args, **kwargs):
        """
        Connect the graphical with the functional control.

        E.g. SpadicControlDial(c.hitlogic, "threshold1", ...)
        """
        mutti.Dial.__init__(self, *args, **kwargs)
        self.control_unit = control_unit
        self.control_param = control_param

    #--------------------------------------------------------------------

    def _set(self): # Dial already has a "set" method...
        self.control_unit.set(**{self.control_param: self.value})

    def apply(self):
        self.control_unit.apply()

    def write(self):
        self._set()
        self.apply()

    def get(self):
        return self.control_unit.get()[self.control_param]

    def update(self):
        self.control_unit.update()

    def read(self):
        self.update()
        return self.get()

    #--------------------------------------------------------------------

    def _changed(self):
        return self.read() != self.value

    #--------------------------------------------------------------------
        
    def _handle_key(self, key):
        key = mutti.Dial._handle_key(self, key)
        if key is not None:
            if key == ord('p'):
                self.write()
            elif key == ord('r'):
                self.value = self.read()
            else:
                return key
        

class SpadicControlUI(mutti.Screen):
    def __init__(self, spadic_controller):
        mutti.Screen.__init__(self)

        c = spadic_controller
        d = SpadicControlDial(c.hitlogic, "threshold1",
                              "Threshold 1", (-256, 255), 4, 15)
        d._status = self.statusbar

        self.adopt(d)

