import curses.ascii
import mutti
from .base import SpadicDial, SpadicToggle
        
#--------------------------------------------------------------------

class MonitorEnableToggle(SpadicToggle):
    def _statuslabel(self):
        return "Monitor enable"
        
#--------------------------------------------------------------------

class MonitorChannelSelect(SpadicDial):
    def _statuslabel(self):
        return "Monitor channel"

    def _displaytext(self):
        g = {0: 'A', 1: 'B'}[self.value//16]
        c = self.value%16
        return "%s.%i" % (g, c)

    def _statustext(self):
        return self._displaytext()

    def inc(self, amount):
        numvalue = self.vmax - self.vmin + 1
        newvalue = (self.value + amount) % numvalue
        self.set_value(self.vmin + newvalue)

    def dec(self, amount):
        numvalue = self.vmax - self.vmin + 1
        newvalue = (self.value - amount) % numvalue
        self.set_value(self.vmin + newvalue)

    def _from_text(self, text):
        try:
            return SpadicDial._from_text(self, text)
        except ValueError:
            try:
                g = {'a': 0, 'b': 1}[text[0].lower()]
                c = int(text[1:].strip(' .'))
                return g*16+c
            except (KeyError, ValueError):
                raise ValueError
        
#--------------------------------------------------------------------

class MonitorSourceToggle(SpadicToggle):
    def set_state(self, state):
        try:
            if state.upper() in ['ADC', 'CSA']:
                self.state = state.upper()
        except AttributeError:
            pass

    def _handle_key(self, key):
        if key == curses.ascii.SP:
            self.set_state({'ADC': 'CSA', 'CSA': 'ADC'}[self.state])
        elif key in self._write_keys:
            self.write()
        elif key in self._read_keys:
            self.set_state(self.read())
        else:
            return key

    def _displaytext(self):
        return self.state

    def _statustext(self):
        return self.state

    def _statuslabel(self):
        return "Monitor source"

    def _helptext(self):
        return "Space to toggle"
        
#--------------------------------------------------------------------

class MonitorFrame(mutti.Frame):
    def __init__(self, spadic_controller, statusbar, _log=None):
        mutti.Frame.__init__(self, "Monitor Bus")
        self.control_panels = []
        self._log = _log

        u = spadic_controller.monitor
        vlist = mutti.VList()

        for d in [MonitorChannelSelect(u, "channel", (0, 31), 4, "Channel",
                                       min_width=20),
                  MonitorSourceToggle(u, "source", "Source", min_width=20),
                  MonitorEnableToggle(u, "enable", "Enable", min_width=20),
                 ]:
            d._status = statusbar
            d._log = _log
            self.control_panels.append(d)
            vlist.adopt(d)
        self.adopt(vlist)

    def _set_all(self):
        for panel in self.control_panels:
            panel.set()

    def _get_all(self):
        for panel in self.control_panels:
            panel._get()

