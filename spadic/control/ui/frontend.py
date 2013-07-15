import curses
import curses.ascii
import mutti
from base import SpadicDial, SpadicToggle

class FrontendToggle(SpadicToggle):
    def __init__(self, xfbpanel, *args, **kwargs):
        self._xfbpanel = xfbpanel
        SpadicToggle.__init__(self, *args, **kwargs)

    def set_state(self, state):
        try:
            if state in 'nNpP':
                self.state = state
        except TypeError:
            self.state = 'P'

    def get(self):
        result = SpadicToggle.get(self)
        self._xfbpanel.label = {'P': '  nFB', 'N': '  pFB'}[result]
        return result

    def _handle_key(self, key):
        if key == ord('+'):
            self.set_state('P')
        elif key == ord('-'):
            self.set_state('N')
        elif key == curses.ascii.SP:
            self.set_state({'N': 'P', 'P': 'N'}[self.state])
        elif key in self._write_keys:
            self.write()
        elif key in self._read_keys:
            self.set_state(self.read())
        else:
            return key

    def _displaytext(self):
        return self.state.upper()

    def _statustext(self):
        return self.state.upper()

    def _helptext(self):
        return "Space to toggle, +/- to set"
        
#--------------------------------------------------------------------

class FrontendFrame(mutti.Frame):
    def __init__(self, spadic_controller, statusbar, _log=None):
        mutti.Frame.__init__(self, "CSA Bias")
        self.control_panels = []
        self._log = _log

        vlist = mutti.VList()
        u = spadic_controller.frontend

        xfbdial = SpadicDial(u, "xfb", (0, 127), 3,
                             "  xFB", min_width=10)

        d = FrontendToggle(xfbdial, u, "frontend",
                           "Frontend polarity", min_width=20)
        d._status = statusbar
        d._log = _log
        self.control_panels.append(d)
        vlist.adopt(d)

        grid = mutti.Grid(2, 3)
        for (i, d) in enumerate([
          SpadicDial(u, "psourcebias", (0, 127), 3,
                     "pSourceBias", min_width=16),
          SpadicDial(u, "nsourcebias", (0, 127), 3,
                     "nSourceBias", min_width=16),
          SpadicDial(u, "pcasc", (0, 127), 3,
                     "  pCasc",     min_width=12),
          SpadicDial(u, "ncasc", (0, 127), 3,
                     "  nCasc",     min_width=12),
          xfbdial,
          ]):
            d._status = statusbar
            d._log = _log
            self.control_panels.append(d)
            grid.adopt(d, row=(i%2), col=(i//2))
        vlist.adopt(grid)

        self.adopt(vlist)

    def _set_all(self):
        for panel in self.control_panels:
            panel.set()

    def _get_all(self):
        for panel in self.control_panels:
            panel._get()

